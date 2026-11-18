import hashlib, hmac, json, time
from urllib.parse import parse_qsl
from fastapi import Header, HTTPException, Depends
from .config import settings

def _secret(bot_token: str) -> bytes:
    return hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()

def verify_init_data(init_data: str) -> dict:
    pairs = dict(parse_qsl(init_data, keep_blank_values=True))
    received = pairs.pop("hash", None)
    if not received:
        raise HTTPException(401, "missing hash")
    check = "\n".join(f"{k}={v}" for k, v in sorted(pairs.items()))
    expected = hmac.new(_secret(settings().bot_token), check.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, received):
        raise HTTPException(401, "bad signature")
    if time.time() - int(pairs.get("auth_date", 0)) > settings().auth_max_age:
        raise HTTPException(401, "stale initData")
    user = json.loads(pairs.get("user", "{}"))
    if not user.get("id"):
        raise HTTPException(401, "no user")
    return user

async def current_user(x_init_data: str = Header(...)) -> dict:
    return verify_init_data(x_init_data)