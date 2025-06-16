from fastapi import Header, HTTPException
import os

# Define a simple API key for authentication.
# In a production environment, this should be a more robust and securely managed key.
# Load API_KEY from an environment variable for security.
# Fallback to a default for local development if not set, but warn about it.
API_KEY = os.getenv("GRAMMAFREE_API_KEY", "12345") # Use a strong default for production!

if API_KEY == "12345":
    print("WARNING: Using default API_KEY. Set GRAMMAFREE_API_KEY environment variable in production!")

def verify_api_key(x_api_key: str = Header(...)):
    """
    Dependency function to verify the API key provided in the request headers.

    Args:
        x_api_key (str): The API key expected in the 'X-API-Key' header.

    Raises:
        HTTPException: If the provided API key does not match the expected API_KEY.
    """
    if x_api_key != API_KEY:
        # Raise an HTTPException with 401 Unauthorized status if the key is invalid.
        raise HTTPException(status_code=401, detail="Unauthorized")
