from typing import Annotated

from pydantic import BaseModel, Field
from pydantic_extra_types.currency_code import ISO4217

from backcat.domain.base import DomainBaseModel
from backcat.domain.id import AreaID
from backcat.domain.point import Point


class Price(BaseModel):
    amount: int = Field(le=100)
    currency: Annotated[str, ISO4217]


class Area(DomainBaseModel[AreaID]):
    polygon: list[Point] = Field(min_length=3)
    description: str | None = Field(max_length=5000)
    price: Price = Field()
