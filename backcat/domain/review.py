from pydantic import Field

from backcat.domain.base import DomainBaseModel
from backcat.domain.id import ReviewID


class Review(DomainBaseModel[ReviewID]):
    rating: int = Field(ge=1, le=5)
    comment: str | None = Field(max_length=5000)
