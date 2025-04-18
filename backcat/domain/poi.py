from pydantic import Field

from backcat.domain.base import DomainBaseModel
from backcat.domain.id import POIID
from backcat.domain.poi_kind import POIKind
from backcat.domain.point import Point


class POI(DomainBaseModel[POIID]):
    kind: POIKind = Field(default=POIKind.GENERAL)
    point: Point = Field()
    name: str = Field(max_length=150)
    description: str | None = Field(max_length=5000)
