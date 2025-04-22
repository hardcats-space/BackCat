from typing import Literal

from pydantic import BaseModel, Field


class JWT(BaseModel):
    secret: str = Field(description="secret key for JWT", min_length=32, max_length=128)
    algorithm: Literal["HS256", "HS384", "HS512"] = Field(description="algorithm for JWT", default="HS256")
    token_expires: int = Field(description="access token expiration time in seconds", default=300, ge=60)
