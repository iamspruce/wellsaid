import os
from fastapi import Header, HTTPException, status, Depends

API_KEY = os.getenv("WELLSAID_API_KEY", "12345")

def verify_api_key(x_api_key: str = Header(...)) -> None:
    if not x_api_key or x_api_key != API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key"
        )