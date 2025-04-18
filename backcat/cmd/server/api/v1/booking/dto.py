from litestar.dto import DTOConfig
from litestar.plugins.pydantic import PydanticDTO
from pydantic import BaseModel

from backcat import domain


class CreateBookingRequest(PydanticDTO[domain.Booking]):
    config = DTOConfig(exclude={"id", "created_at", "updated_at", "deleted_at"})


class CreateBookingResponse(PydanticDTO[domain.Booking]):
    config = DTOConfig()


class UpdateBookingRequest(PydanticDTO[domain.Booking]):
    config = DTOConfig(exclude={"id", "created_at", "updated_at", "deleted_at"}, partial=True)


class UpdateBookingResponse(PydanticDTO[domain.Booking]):
    config = DTOConfig()


class ReadBookingResponse(PydanticDTO[domain.Booking]):
    config = DTOConfig()


class _ReadManyBookings(BaseModel):
    data: list[domain.Booking]


class ReadManyBookingResponse(PydanticDTO[_ReadManyBookings]):
    config = DTOConfig()
