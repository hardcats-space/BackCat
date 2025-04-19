from litestar.dto import DTOConfig
from litestar.plugins.pydantic import PydanticDTO
from pydantic import BaseModel

from backcat import domain


class CreateBookingRequest(PydanticDTO[domain.Booking]):
    config = DTOConfig(exclude={"id", "created_at", "updated_at", "deleted_at"}, rename_strategy="camel")


class CreateBookingResponse(PydanticDTO[domain.Booking]):
    config = DTOConfig(rename_strategy="camel")


class UpdateBookingRequest(PydanticDTO[domain.Booking]):
    config = DTOConfig(exclude={"id", "created_at", "updated_at", "deleted_at"}, partial=True, rename_strategy="camel")


class UpdateBookingResponse(PydanticDTO[domain.Booking]):
    config = DTOConfig(rename_strategy="camel")


class ReadBookingResponse(PydanticDTO[domain.Booking]):
    config = DTOConfig(rename_strategy="camel")


class _ReadManyBookings(BaseModel):
    data: list[domain.Booking]


class ReadManyBookingResponse(PydanticDTO[_ReadManyBookings]):
    config = DTOConfig(rename_strategy="camel")
