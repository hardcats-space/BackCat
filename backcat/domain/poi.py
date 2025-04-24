from typing import Any

from pydantic import Field, model_validator

from backcat.domain.base import DomainBaseModel
from backcat.domain.id import POIID
from backcat.domain.poi_kind import POIKind
from backcat.domain.point import Point


class POI(DomainBaseModel[POIID]):
    kind: POIKind = Field(default=POIKind.GENERAL)
    point: Point = Field()
    name: str = Field(max_length=150)
    description: str | None = Field(max_length=5000)

    @model_validator(mode="before")
    @classmethod
    def build_from_flat(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if "lat" in data and "lon" in data:
                data["point"] = Point(lat=data["lat"], lon=data["lon"])
                return data

        return data
