import random
from datetime import datetime, UTC, timedelta
from typing import Self

from msgspec import ValidationError
from polyfactory.factories.pydantic_factory import ModelFactory
from pydantic import Field, model_validator

from backcat.domain.base import DomainBaseModel, BaseFieldsFactory
from backcat.domain.id import BookingID


class Booking(DomainBaseModel[BookingID]):
    booked_since: datetime = Field()
    booked_till: datetime = Field()

    @model_validator(mode="after")
    def _(self) -> Self:
        if self.booked_since.tzinfo is None:
            raise ValidationError("booked_since must contain timezone")

        if self.booked_till.tzinfo is None:
            raise ValidationError("booked_till must contain timezone")

        if self.booked_till < self.booked_since:
            raise ValidationError("booked_till cannot be before booked_since")

        if self.booked_till == self.booked_since:
            raise ValidationError("booked_till cannot be equal booked_since")

        return self


class BookingFactory(ModelFactory[Booking], BaseFieldsFactory):
    @classmethod
    def booked_since(cls) -> datetime:
        return datetime.now(UTC) + timedelta(days=random.randint(5, 15))

    @classmethod
    def booked_till(cls) -> datetime:
        return datetime.now(UTC) + timedelta(days=random.randint(16, 25))
