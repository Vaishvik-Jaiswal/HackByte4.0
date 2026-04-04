from pydantic import BaseModel
from app.schemas.user import User

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: User

class TokenRefresh(BaseModel):
    refresh_token: str

class LoginRequest(BaseModel):
    identifier: str # email or username
    password: str
