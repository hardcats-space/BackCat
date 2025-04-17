from pydantic import Field

from backcat.domain.base import DomainBaseModel
from backcat.domain.id import UserID


class User(DomainBaseModel[UserID]):
    name: str = Field(max_length=150)
    avatar: str | None = Field(default=None)
