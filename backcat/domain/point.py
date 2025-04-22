from polyfactory.factories.pydantic_factory import ModelFactory
from pydantic import BaseModel


class Point(BaseModel):
    lat: float
    lon: float


class PointFactory(ModelFactory[Point]):
    @classmethod
    def lat(cls):
        return cls.__random__.random() * 41 + 41

    @classmethod
    def lon(cls):
        return cls.__random__.random() * 150 + 19
