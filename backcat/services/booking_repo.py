from datetime import datetime
from typing import Protocol, TypedDict, Unpack

from backcat import domain
from backcat.services.cache import Cache, Keyspace


class UpdateBooking(TypedDict):
    booked_since: datetime
    booked_till: datetime


class BookingRepo(Protocol):
    async def create_booking(
        self, booking: domain.Booking, area_id: domain.AreaID, user_id: domain.UserID
    ) -> domain.Booking: ...
    async def read_booking(self, booking_id: domain.BookingID) -> domain.Booking | None: ...
    async def read_bookings(self, area_id: domain.AreaID, user_id: domain.UserID) -> list[domain.Booking]: ...
    async def update_booking(self, booking_id: domain.BookingID, **update: Unpack[UpdateBooking]) -> domain.Booking: ...
    async def delete_booking(self, booking_id: domain.BookingID) -> domain.Booking: ...


class BookingRepoImpl:
    def __init__(self, cache: Cache):
        self._ks = Keyspace("booking")
        self._cache = cache

    async def create_booking(
        self, booking: domain.Booking, area_id: domain.AreaID, user_id: domain.UserID
    ) -> domain.Booking: ...

    async def read_booking(self, booking_id: domain.BookingID) -> domain.Booking | None: ...

    async def read_bookings(self, area_id: domain.AreaID, user_id: domain.UserID) -> list[domain.Booking]: ...

    async def update_booking(self, booking_id: domain.BookingID, **update: Unpack[UpdateBooking]) -> domain.Booking: ...

    async def delete_booking(self, booking_id: domain.BookingID) -> domain.Booking: ...
