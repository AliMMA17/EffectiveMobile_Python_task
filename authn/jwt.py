from __future__ import annotations
import os
import datetime as dt
from typing import Optional, Tuple, Dict, Any
import jwt

JWT_SECRET = os.getenv("JWT_SECRET", "dev")
JWT_ALG = os.getenv("JWT_ALG", "HS256")
JWT_EXPIRES_MIN = int(os.getenv("JWT_EXPIRES_MIN", "60"))

def make_jwt(user_id: int) -> str:
    now = dt.datetime.utcnow()
    exp = now + dt.timedelta(minutes=JWT_EXPIRES_MIN)
    payload = {"sub": str(user_id), "iat": int(now.timestamp()), "exp": int(exp.timestamp())}
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALG)
    return token if isinstance(token, str) else token.decode("utf-8")

def verify_jwt(token: str) -> Optional[dict]:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALG])
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

# New: verbose checker to show the exact error/payload
def verify_jwt_verbose(token: str) -> Dict[str, Any]:
    out: Dict[str, Any] = {"ok": False, "alg": JWT_ALG}
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALG])
        out["ok"] = True
        out["payload"] = payload
        return out
    except Exception as e:
        out["error"] = repr(e)
        return out
