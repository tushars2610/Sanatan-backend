from typing import Optional
from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    phone_number: str = Field(..., pattern=r"^\+?[1-9]\d{9,14}$", description="Phone number to log in or register directly")
    full_name: Optional[str] = Field(default=None, description="Optional user name")


class SendOtpRequest(BaseModel):
    phone_number: str = Field(..., pattern=r"^\+?[1-9]\d{9,14}$", description="E.164 or 10-digit Indian phone number")


class SendOtpResponse(BaseModel):
    success: bool = True
    message: str
    phone_number: str
    expires_in_seconds: int = 300
    dev_otp: Optional[str] = "123456"


class VerifyOtpRequest(BaseModel):
    phone_number: str = Field(..., pattern=r"^\+?[1-9]\d{9,14}$")
    otp: Optional[str] = Field(default="123456", description="OTP code (optional, verification bypassed)")


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    is_new_user: bool = False
