import os
import logging
from fastapi import Header, HTTPException, status

API_KEY = os.getenv("WELLSAID_API_KEY", "12345")

def verify_api_key(x_api_key: str = Header(...)) -> None:
    if not x_api_key or x_api_key != API_KEY:
        logging.warning("Unauthorized access attempt with key: %s", x_api_key)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key"
        )
