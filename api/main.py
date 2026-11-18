from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import select, desc
from .config import settings
from .auth import current_user
from .models import User, Job, Hit
from .db import session, init_db
from . import sweep

app = FastAPI(title="SeedHunter")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings().allowed_origins.split(","),
    allow_credentials=True, allow_methods=["*"], allow_headers=["*"],
)

@app.on_event("startup")
async def _boot(): await init_db()

@app.post("/auth/telegram")
async def login(user=Depends(current_user)):
    async with session() as s:
        row = await s.get(User, user["id"])
        if not row:
            row = User(id=user["id"], username=user.get("username"))
            s.add(row); await s.commit()
        return {"id": row.id, "credits": row.credits}

class JobIn(BaseModel):
    mode: str
    shard: str
    rate: int = 0

@app.post("/jobs")
async def create_job(body: JobIn, user=Depends(current_user)):
    if body.mode not in ("biased", "replay", "target"):
        raise HTTPException(422, "bad mode")
    async with session() as s:
        j = Job(user_id=user["id"], mode=body.mode, shard=body.shard, rate=body.rate)
        s.add(j); await s.commit()
        await sweep.enqueue(j.id, body.model_dump())
        return {"id": str(j.id)}

@app.get("/jobs")
async def list_jobs(user=Depends(current_user)):
    async with session() as s:
        q = select(Job).where(Job.user_id == user["id"]).order_by(desc(Job.created)).limit(50)
        return [{"id": str(j.id), "mode": j.mode, "status": j.status} for j in (await s.scalars(q))]

@app.get("/hits")
async def list_hits(user=Depends(current_user)):
    async with session() as s:
        q = (select(Hit).join(Job, Hit.job_id == Job.id)
             .where(Job.user_id == user["id"]).order_by(desc(Hit.usd)).limit(100))
        return [{"id": str(h.id), "address": h.address, "usd": float(h.usd), "chain": h.chain}
                for h in (await s.scalars(q))]

@app.post("/hits/{hit_id}/plan")
async def plan(hit_id: str, user=Depends(current_user)):
    async with session() as s:
        h = await s.get(Hit, hit_id)
        if not h: raise HTTPException(404)
        return await sweep.build_psbt(h)

@app.get("/stats")
async def stats():
    async with session() as s:
        jobs = len((await s.scalars(select(Job))).all())
        hits = len((await s.scalars(select(Hit))).all())
        return {"jobs": jobs, "hits": hits}