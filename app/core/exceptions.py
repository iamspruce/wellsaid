# app/core/exceptions.py
from fastapi import HTTPException


class ServiceError(HTTPException):
    """
    Base exception for general service-related errors.
    Inherits from HTTPException to allow direct use in FastAPI responses.
    """
    def __init__(self, status_code: int, detail: str, error_type: str = "ServiceError"):
        super().__init__(status_code=status_code, detail=detail)
        self.error_type = error_type

    def to_dict(self):
        """Returns a dictionary representation of the exception."""
        return {
            "detail": self.detail,
            "status_code": self.status_code,
            "error_type": self.error_type
        }


class ModelNotDownloadedError(ServiceError):
    """
    Raised when a required model is not found locally.
    Informs the client that a download is necessary.
    """
    def __init__(self, model_id: str, feature_name: str, detail: str = None):
        detail = detail or f"Model '{model_id}' required for '{feature_name}' is not downloaded."
        super().__init__(status_code=424, detail=detail, error_type="ModelNotDownloaded")
        self.model_id = model_id
        self.feature_name = feature_name

    def to_dict(self):
        base_dict = super().to_dict()
        base_dict.update({
            "model_id": self.model_id,
            "feature_name": self.feature_name
        })
        return base_dict


class ModelDownloadFailedError(ServiceError):
    """Exception raised when a model download operation fails."""
    def __init__(self, model_id: str, feature_name: str, original_error: str = "Unknown error"):
        super().__init__(
            status_code=503, # Service Unavailable
            detail=f"Failed to download model '{model_id}' for '{feature_name}'. Please check your internet connection or try again. Error: {original_error}",
            error_type="ModelDownloadFailed",
            model_id=model_id,
            feature_name=feature_name
        )
        self.original_error = original_error