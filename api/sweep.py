import json
from .config import settings

async def enqueue(job_id, payload):
    import redis.asyncio as aioredis
    r = aioredis.from_url(settings().redis_url)
    await r.lpush("jobs", json.dumps({"id": str(job_id), **payload}))
    await r.aclose()

async def build_psbt(hit):
    # full tree already expanded host-side on hit; build unsigned sweep
    # python-bitcoinlib -> PSBT with one input, fee-bumped output, no broadcast
    return {"hit": str(hit.id), "address": hit.address, "psbt": None, "note": "sign locally, do not broadcast yet"}