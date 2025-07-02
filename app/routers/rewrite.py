# app/routers/rewrite.py
import logging
from fastapi import APIRouter, Depends, HTTPException, status # Import HTTPException and status for validation

from app.schemas.base import RewriteRequest # Assuming this Pydantic model exists
from app.services.gpt4_rewrite import GPT4Rewriter # Import the service class
from app.core.security import verify_api_key # Assuming API key verification is still used
from app.core.config import APP_NAME # For logger naming
from app.core.exceptions import ServiceError # For re-raising internal errors

logger = logging.getLogger(f"{APP_NAME}.routers.rewrite")

router = APIRouter(prefix="/rewrite", tags=["Rewrite"])

# Initialize service instance once per application lifecycle
gpt4_rewriter_service = GPT4Rewriter()


@router.post("/with_instruction", dependencies=[Depends(verify_api_key)]) # Changed path to /with_instruction for clarity
async def rewrite_with_instruction_endpoint(payload: RewriteRequest):
    """
    Rewrites the provided text based on a specific instruction using GPT-4.
    Requires an OpenAI API key.
    """
    text = payload.text.strip()
    instruction = payload.instruction.strip()
    user_api_key = payload.user_api_key # The user's provided API key

    # Basic input validation for clarity, though service also validates
    if not text:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Input text cannot be empty.")
    if not instruction:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Instruction cannot be empty.")
    if not user_api_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="OpenAI API key is required for this feature.")


    logger.info(f"Received rewrite request for text (first 50 chars): '{text[:50]}...' with instruction (first 50 chars): '{instruction[:50]}...'")

    try:
        # Directly call the async service method
        # ServiceError will be raised here if there's an issue (e.g., missing API key, OpenAI API error),
        # and caught by the global exception handler in app/main.py.
        result = await gpt4_rewriter_service.rewrite(
            text=text,
            instruction=instruction,
            user_api_key=user_api_key # Pass the user's API key
        )

        logger.info(f"Rewriting successful for text (first 50 chars): '{text[:50]}...'")
        return {"rewrite": result} # Consistent key for response

    except ServiceError as e:
        # Re-raise ServiceError. It will be caught by the global exception handler.
        raise e
    except Exception as e:
        # Catch any unexpected exceptions and re-raise as a generic ServiceError
        logger.exception(f"Unhandled error in rewriting endpoint for text: '{text[:50]}...'")
        raise ServiceError(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred during rewriting.") from e