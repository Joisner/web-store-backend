from pydantic import BaseModel
from typing import Optional

class Token(BaseModel):
    access_token: str
    token_type: str
    refresh_token: Optional[str] = None # If you implement refresh tokens

class TokenData(BaseModel):
    # 'sub' (subject) is typically the user's ID or email
    sub: Optional[str] = None

class RefreshToken(BaseModel):
    refresh_token: str
