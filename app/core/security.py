from fastapi import Header, HTTPException

# Define a simple API key for authentication.
# In a production environment, this should be a more robust and securely managed key.
API_KEY = "12345"

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
