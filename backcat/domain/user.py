from pydantic import EmailStr, Field

from backcat.domain.base import DomainBaseModel
from backcat.domain.id import UserID


class User(DomainBaseModel[UserID]):
    email: EmailStr
    name: str = Field(min_length=1, max_length=150)
    password: str = Field(min_length=8)
    thumbnail: str | None = Field(default=None)
