from datetime import UTC, datetime
from typing import Any
from typing import Protocol, TypedDict, Unpack

from asyncpg import DataError, UniqueViolationError
from piccolo.columns import Column

from backcat import domain
from backcat.database import tables
from backcat.database.projector import ProjectionError, projection
from backcat.services import errors
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
    ) -> domain.Booking:
        try:
            db_booking = projection(booking, area_id=area_id, user_id=user_id)
        except ProjectionError as e:
            raise errors.ValidationError("invalid booking") from e
        except Exception as e:
            raise errors.InternalServerError("failed to insert booking") from e

        try:
            async with tables.Booking._meta.db.transaction():
                db_booking = (await tables.Booking.insert(db_booking).returning(*tables.Booking.all_columns()).run())[0]
                domain_booking = projection(db_booking, cast_to=domain.Booking)

                await self._cache.set(self._ks.key(domain_booking.id.hex), domain_booking, expire=self._cache.HOT_FEAT)

                return domain_booking
        except UniqueViolationError as e:
            raise errors.ConflictError("booking already exists") from e
        except DataError as e:
            raise errors.ConflictError("invalid data object") from e
        except IndexError as e:
            raise errors.InternalServerError("insertion failed") from e
        except ProjectionError as e:
            raise errors.ConversionError("invalid booking") from e
        except Exception as e:
            raise errors.InternalServerError("failed to insert booking") from e

    async def read_booking(self, booking_id: domain.BookingID) -> domain.Booking | None:
        try:
            domain_booking = await self._cache.get(self._ks.key(booking_id.hex), t=domain.Booking)
            if domain_booking is not None:
                return domain_booking

            db_booking = (
                await tables.Booking.objects()
                .where(
                    tables.Booking.id == booking_id,
                    tables.Booking.deleted_at.is_null(),
                )
                .first()
                .run()
            )
            if db_booking is None:
                return None

            return projection(db_booking)
        except ProjectionError as e:
            raise errors.InternalServerError("failed to read booking") from e
        except Exception as e:
            raise errors.InternalServerError("failed to read booking") from e

    async def read_bookings(self, area_id: domain.AreaID, user_id: domain.UserID) -> list[domain.Booking]:
        try:
            db_bookings = (
                await tables.Booking.objects()
                .where(
                    tables.Booking.area == area_id,
                    tables.Booking.user == user_id,
                    tables.Booking.deleted_at.is_null(),
                )
                .run()
            )
            return [projection(db_booking) for db_booking in db_bookings]
        except ProjectionError as e:
            raise errors.InternalServerError("failed to read bookings") from e
        except Exception as e:
            raise errors.InternalServerError("failed to read bookings") from e

    async def update_booking(self, booking_id: domain.BookingID, update: dict[str, Any]) -> domain.Booking:
        try:
            await self._cache.invalidate(self._ks.key(booking_id.hex))

            values: dict[Column | str, Any] = {}
            if "booked_since" in update:
                values[tables.Booking.booked_since] = update["booked_since"]
            if "booked_till" in update:
                values[tables.Booking.booked_till] = update["booked_till"]

            async with tables.Booking._meta.db.transaction():
                db_booking = (
                    await tables.Booking.update(values)
                    .where(tables.Booking.id == booking_id, tables.Booking.deleted_at.is_null())
                    .returning(*tables.Booking.all_columns())
                    .run()
                )[0]

                domain_booking = projection(db_booking, cast_to=domain.Booking)

                await self._cache.set(self._ks.key(domain_booking.id.hex), domain_booking, expire=self._cache.HOT_FEAT)

            return domain_booking
        except DataError as e:
            raise errors.ConflictError("invalid data object") from e
        except IndexError as e:
            raise errors.InternalServerError("update failed") from e
        except ProjectionError as e:
            raise errors.ValidationError("invalid booking") from e
        except Exception as e:
            raise errors.InternalServerError("failed to update booking") from e

    async def delete_booking(self, booking_id: domain.BookingID) -> domain.Booking:
        try:
            await self._cache.invalidate(self._ks.key(booking_id.hex))

            async with tables.Booking._meta.db.transaction():
                db_booking = (
                    await tables.Booking.update({tables.Booking.deleted_at: datetime.now(UTC)})
                    .where(tables.Booking.id == booking_id, tables.Booking.deleted_at.is_null())
                    .returning(*tables.Booking.all_columns())
                    .run()
                )[0]

                domain_booking = projection(db_booking, cast_to=domain.Booking)

                await self._cache.set(self._ks.key(domain_booking.id.hex), domain_booking, expire=self._cache.HOT_FEAT)

            return domain_booking
        except IndexError as e:
            raise errors.NotFoundError("no such booking found") from e
        except DataError as e:
            raise errors.ConflictError("invalid data object") from e
        except ProjectionError as e:
            raise errors.ValidationError("invalid booking") from e
        except Exception as e:
            raise errors.InternalServerError("failed to delete booking") from e
