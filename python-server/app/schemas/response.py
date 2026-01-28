"""Standard response schemas for API endpoints"""
from pydantic import BaseModel
from typing import Any


class StandardResponse(BaseModel):
    """
    Undetectable-compatible response format.

    Success response:
        {"code": 0, "status": "success", "data": {...}}

    Error response:
        {"code": 1, "status": "error", "data": {"error": "message"}}
    """

    code: int  # 0 = success, 1 = error
    status: str  # "success" or "error"
    data: Any  # Response data or error object

    @classmethod
    def success(cls, data: Any = None) -> "StandardResponse":
        """Create success response"""
        return cls(code=0, status="success", data=data or {})

    @classmethod
    def error(cls, message: str) -> "StandardResponse":
        """Create error response"""
        return cls(code=1, status="error", data={"error": message})
