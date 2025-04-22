from polyfactory import Use
from polyfactory.factories.pydantic_factory import ModelFactory
from pydantic import Field

from backcat.domain.base import DomainBaseModel, BaseFieldsFactory
from backcat.domain.id import POIID
from backcat.domain.poi_kind import POIKind
from backcat.domain.point import Point, PointFactory


class POI(DomainBaseModel[POIID]):
    kind: POIKind = Field(default=POIKind.GENERAL)
    point: Point = Field()
    name: str = Field(max_length=150)
    description: str | None = Field(max_length=5000)


class POIFactory(ModelFactory[POI], BaseFieldsFactory):
    @classmethod
    def kind(cls):
        return cls.__random__.choice(list(POIKind))

    @classmethod
    def point(cls):
        return PointFactory.build()

    @classmethod
    def name(cls):
        return cls.__random__.choice(["POI 1", "POI 2", "POI 3"])

    @classmethod
    def description(cls):
        return cls.__random__.choice(["Nice place", "Beautiful place", "Great place"])
