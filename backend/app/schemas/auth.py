from typing import Optional
from pydantic import EmailStr, Field
from app.schemas.common import BaseSchema
from app.schemas.user import UserOut


class Token(BaseSchema):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserOut


class TokenData(BaseSchema):
    user_id: Optional[str] = None
    role: Optional[str] = None


class LoginRequest(BaseSchema):
    email: EmailStr
    password: str = Field(..., min_length=1)


class RegisterRequest(BaseSchema):
    email: EmailStr
    full_name: str = Field(..., min_length=2, max_length=120)
    password: str = Field(..., min_length=6, max_length=100)
    role: str = Field(default="citizen")  # citizen, ngo, volunteer, admin
    phone_number: Optional[str] = None
    organization_id: Optional[str] = None
