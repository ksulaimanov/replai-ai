import os
from fastapi import Header, HTTPException

_KEY = os.getenv("INTERNAL_API_KEY", "")


def verify_internal_key(x_internal_key: str = Header(...)):
    if not _KEY or x_internal_key != _KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")
