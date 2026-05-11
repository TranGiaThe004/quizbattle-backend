from pydantic import BaseModel
from typing import Any, Optional

class StandardResponse(BaseModel):
    success: bool = True
    data: Optional[Any] = None
    message: str = "OK"

class ErrorResponse(BaseModel):
    success: bool = False
    error_code: str
    message: str