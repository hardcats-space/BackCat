from typing import Annotated, Any

from pydantic import BaseModel, Field, model_validator
from pydantic_extra_types.currency_code import ISO4217

from backcat.domain.base import DomainBaseModel
from backcat.domain.id import AreaID
from backcat.domain.point import Point


class Price(BaseModel):
    amount: int = Field(ge=100)
    currency: Annotated[str, ISO4217]


class Area(DomainBaseModel[AreaID]):
    polygon: list[Point] = Field(min_length=3)
    description: str | None = Field(max_length=5000)
    price: Price = Field()

    @model_validator(mode="before")
    @classmethod
    def build_from_flat(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if "price" not in data or not isinstance(data["price"], dict | Price):
                data["price"] = {
                    "amount": data.get("price_amount"),
                    "currency": data.get("price_currency"),
                }

        return data
