from typing import Optional, Any, AnyStr, Dict
from pydantic import BaseModel, Field


class CodeRequest(BaseModel):
    phone_number: str


class CodeVerifyRequest(BaseModel):
    phone_number: str
    code: str
    phone_code_hash: str


class PasswordVerifyRequest(BaseModel):
    phone_number: str
    password: str


class APIResponse(BaseModel):
    success: bool
    error: Optional[str] = None
    data: Dict[AnyStr, Any] = Field(default_factory=dict)
