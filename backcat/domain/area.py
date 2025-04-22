from typing import Annotated

from polyfactory import Use
from polyfactory.factories.pydantic_factory import ModelFactory
from pydantic import BaseModel, Field
from pydantic_extra_types.currency_code import ISO4217

from backcat.domain.base import DomainBaseModel, BaseFieldsFactory
from backcat.domain.id import AreaID
from backcat.domain.point import Point, PointFactory


class Price(BaseModel):
    amount: int
    currency: Annotated[str, ISO4217]


class Area(DomainBaseModel[AreaID]):
    polygon: list[Point] = Field(min_length=3)
    description: str | None = Field(max_length=5000)
    price: Price = Field()


class AreaFactory(ModelFactory[Area], BaseFieldsFactory):
    polygon = Use(PointFactory.batch, size=3)

    @classmethod
    def description(cls):
        return cls.__random__.choice(["Nice place", "Beautiful place", "Great place"])

    @classmethod
    def price(cls):
        return Price(
            amount=cls.__random__.randint(1, 100) * 10,
            currency=cls.__random__.choice(["USD", "EUR", "RUB"]),
        )
