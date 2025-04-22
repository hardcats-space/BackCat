from polyfactory.factories.pydantic_factory import ModelFactory
from pydantic import Field

from backcat.domain.base import DomainBaseModel, BaseFieldsFactory
from backcat.domain.id import ReviewID


class Review(DomainBaseModel[ReviewID]):
    rating: int = Field(ge=1, le=5)
    comment: str | None = Field(max_length=5000)


class ReviewFactory(ModelFactory[Review], BaseFieldsFactory):
    @classmethod
    def rating(cls):
        return cls.__random__.choice([1, 2, 3, 4, 5])

    @classmethod
    def comment(cls):
        return cls.__random__.choice(
            [
                "Nice place",
                "Beautiful place",
                "Great place",
                "Not so good",
                "Bad place",
            ]
        )
