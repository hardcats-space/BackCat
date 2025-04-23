from typing import Annotated, Any

import litestar
from dishka.integrations.litestar import FromDishka, inject
from litestar.dto import DTOData
from litestar.exceptions import NotFoundException
from litestar.params import Parameter

from backcat import domain, services
from backcat.cmd.server.api.v1.booking import dto


class Controller(litestar.Controller):
    path = "/booking"
    tags = ["booking"]

    @litestar.post("", dto=dto.CreateBookingRequest, return_dto=dto.CreateBookingResponse)
    @inject
    async def create(
        self,
        area_id: Annotated[domain.AreaID, Parameter(query="areaId")],
        data: DTOData[domain.Booking],
        request: litestar.Request[domain.User, Any, Any],
        booking_repo: FromDishka[services.BookingRepo],
    ) -> domain.Booking:
        return await booking_repo.create_booking(
            request.user.id,
            data.create_instance(**domain.Booking.new_defaults_kwargs()),
            area_id,
        )

    @litestar.get("/{id:uuid}", return_dto=dto.ReadBookingResponse)
    @inject
    async def read_one(
        self,
        id: domain.BookingID,
        request: litestar.Request[domain.User, Any, Any],
        booking_repo: FromDishka[services.BookingRepo],
    ) -> domain.Booking:
        booking = await booking_repo.read_booking(request.user.id, id)
        if booking is None:
            raise NotFoundException(detail="booking not found")
        return booking

    @litestar.get("", return_dto=dto.ReadManyBookingResponse)
    @inject
    async def read_many(
        self,
        area_id: Annotated[domain.AreaID, Parameter(query="areaId")],
        request: litestar.Request[domain.User, Any, Any],
        booking_repo: FromDishka[services.BookingRepo],
    ) -> dto._ReadManyBookings:
        return dto._ReadManyBookings(
            data=await booking_repo.filter_booking(
                request.user.id,
                services.booking_repo.FilterBooking(area_id=area_id),
            )
        )

    @litestar.patch("/{id:uuid}", dto=dto.UpdateBookingRequest, return_dto=dto.UpdateBookingResponse)
    @inject
    async def update(
        self,
        id: domain.BookingID,
        data: DTOData[domain.Booking],
        request: litestar.Request[domain.User, Any, Any],
        booking_repo: FromDishka[services.BookingRepo],
    ) -> domain.Booking:
        return await booking_repo.update_booking(
            request.user.id,
            id,
            services.booking_repo.UpdateBooking.model_validate(data.as_builtins()),
        )

    @litestar.delete("/{id:uuid}")
    @inject
    async def delete(
        self,
        id: domain.BookingID,
        request: litestar.Request[domain.User, Any, Any],
        booking_repo: FromDishka[services.BookingRepo],
    ) -> None:
        await booking_repo.delete_booking(request.user.id, id)
