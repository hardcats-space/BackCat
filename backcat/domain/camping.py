from pydantic import Field

from backcat.domain.base import DomainBaseModel
from backcat.domain.id import CampingID
from backcat.domain.point import Point


class Camping(DomainBaseModel[CampingID]):
    polygon: list[Point] = Field(min_length=3)
    title: str = Field(max_length=250)
    description: str = Field(max_length=5000)
