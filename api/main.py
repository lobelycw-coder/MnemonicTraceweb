from fastapi import FastAPI
from sqlalchemy import text

from adapters.db.session import session_factory

app = FastAPI(title="MnemonicTrace")


@app.get("/healthz")
async def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/stats")
async def stats() -> dict[str, int]:
    async with session_factory() as session:
        rows = (await session.execute(
            text("SELECT status, count(*) FROM shards GROUP BY status")
        )).all()
        hits = (await session.execute(text("SELECT count(*) FROM hits"))).scalar_one()
    counts = {status: n for status, n in rows}
    return {
        "pending": counts.get("pending", 0),
        "running": counts.get("running", 0),
        "done": counts.get("done", 0),
        "hits": hits,
    }


@app.get("/hits")
async def hits(limit: int = 50) -> list[dict]:
    async with session_factory() as session:
        rows = (await session.execute(
            text("SELECT chain, address, balance FROM hits ORDER BY id DESC LIMIT :l"),
            {"l": min(limit, 200)},
        )).all()
    return [{"chain": c, "address": a, "balance": b} for c, a, b in rows]