import litestar
from litestar.dto import DTOData

from backcat import domain
from backcat.cmd.server.api.v1.booking import dto


class Controller(litestar.Controller):
    path = "/booking"

    @litestar.post("", dto=dto.CreateBookingRequest, return_dto=dto.CreateBookingResponse)
    async def create(self, data: DTOData[domain.Booking], area_id: domain.AreaID) -> domain.Booking:
        return domain.booking.BookingFactory.build()

    @litestar.get("/{id:uuid}", return_dto=dto.ReadBookingResponse)
    async def read_one(self, id: domain.BookingID) -> domain.Booking:
        return domain.booking.BookingFactory.build()

    @litestar.get("", return_dto=dto.ReadManyBookingResponse)
    async def read_many(self, area_id: domain.AreaID) -> dto._ReadManyBookings:
        return dto._ReadManyBookings(
            data=[domain.booking.BookingFactory.build() for i in range(3)]
        )

    @litestar.patch("/{id:uuid}", dto=dto.UpdateBookingRequest, return_dto=dto.UpdateBookingResponse)
    async def update(self, id: domain.BookingID, data: DTOData[domain.Booking]) -> domain.Booking:
        return domain.booking.BookingFactory.build()

    @litestar.delete("/{id:uuid}")
    async def delete(self, id: domain.BookingID) -> None:
        return None
