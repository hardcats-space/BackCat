from pydantic import Field

from backcat.domain.base import DomainBaseModel
from backcat.domain.id import AreaID
from backcat.domain.point import Point


class Area(DomainBaseModel[AreaID]):
    polygon: list[Point] = Field(min_length=3)
