from pydantic import Field, field_validator

from backcat.domain.base import DomainBaseModel
from backcat.domain.id import CampingID
from backcat.domain.point import Point


class Camping(DomainBaseModel[CampingID]):
    polygon: list[Point] = Field(min_length=3)
    title: str = Field(max_length=250)
    description: str | None = Field(max_length=5000)
    thumbnails: list[str] = Field(default_factory=list, min_length=0, max_length=5)

    @field_validator("thumbnails", mode="after")
    @classmethod
    def _(cls, value: list[str]) -> list[str]:
        for thumbnail in value:
            if len(thumbnail) > 255:
                raise ValueError("thumbnails must be less than 255 characters")
        return value
