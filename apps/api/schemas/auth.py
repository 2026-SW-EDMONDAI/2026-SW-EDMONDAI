from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenData(BaseModel):
    accessToken: str
    tokenType: str = "bearer"
