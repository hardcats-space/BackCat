from polyfactory import Use
from polyfactory.factories.pydantic_factory import ModelFactory
from pydantic import Field, field_validator

from backcat.domain.base import DomainBaseModel, BaseFieldsFactory
from backcat.domain.id import CampingID
from backcat.domain.point import Point, PointFactory


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


class CampingFactory(ModelFactory[Camping], BaseFieldsFactory):
    polygon = Use(PointFactory.batch, size=3)

    @classmethod
    def description(cls):
        return cls.__random__.choice(["Nice place", "Beautiful place", "Great place"])

    @classmethod
    def title(cls):
        return cls.__random__.choice(["Camping 1", "Camping 2", "Camping 3"])

    @classmethod
    def thumbnails(cls):
        return [
            cls.__random__.choice(
                [
                    "https://get.wallhere.com/photo/nature-landscape-mountains-obersee-lake-Germany-trees-dead-trees-2286330.jpg",
                    "https://i.pinimg.com/originals/e2/ec/31/e2ec318333608d137b47ce8f2a83eed0.jpg",
                    "https://img3.wallspic.com/attachments/originals/8/0/5/5/45508-sciences-ciel-le_lac_peyto-ecosysteme-les_reliefs_montagneux-4096x2725.jpg",
                ]
            ),
            cls.__random__.choice(
                [
                    "https://get.wallhere.com/photo/nature-landscape-mountains-obersee-lake-Germany-trees-dead-trees-2286330.jpg",
                    "https://i.pinimg.com/originals/e2/ec/31/e2ec318333608d137b47ce8f2a83eed0.jpg",
                    "https://img3.wallspic.com/attachments/originals/8/0/5/5/45508-sciences-ciel-le_lac_peyto-ecosysteme-les_reliefs_montagneux-4096x2725.jpg",
                ]
            )
        ]
