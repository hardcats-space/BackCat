from datetime import UTC, datetime
from typing import Any
from typing import Protocol

from asyncpg import DataError, UniqueViolationError
from piccolo.columns import Column
from pydantic import BaseModel

from backcat import database
from backcat import domain
from backcat.database.projector import ProjectionError, projection
from backcat.services import errors
from backcat.services.cache import Cache, Keyspace


class UpdateBooking(BaseModel):
    booked_since: datetime
    booked_till: datetime


class FilterBooking(BaseModel):
    area_id: domain.AreaID | None


class BookingRepo(Protocol):
    async def create_booking(
        self,
        actor: domain.UserID,
        booking: domain.Booking,
        area_id: domain.AreaID,
    ) -> domain.Booking: ...

    async def read_booking(
        self,
        actor: domain.UserID,
        booking_id: domain.BookingID,
    ) -> domain.Booking | None: ...

    async def update_booking(
        self,
        actor: domain.UserID,
        booking_id: domain.BookingID,
        update: UpdateBooking,
    ) -> domain.Booking: ...

    async def delete_booking(
        self,
        actor: domain.UserID,
        booking_id: domain.BookingID,
    ) -> domain.Booking: ...

    async def filter_booking(
        self,
        actor: domain.UserID,
        filter: FilterBooking,
    ) -> list[domain.Booking]: ...


class BookingRepoImpl(BookingRepo):
    def __init__(self, cache: Cache):
        self._ks = Keyspace("booking")
        self._cache = cache

    async def create_booking(
        self,
        actor: domain.UserID,
        booking: domain.Booking,
        area_id: domain.AreaID,
    ) -> domain.Booking:
        try:
            db_booking = projection(booking, area_id=area_id, user_id=actor)
        except ProjectionError as e:
            raise errors.ValidationError("invalid booking") from e
        except Exception as e:
            raise errors.InternalServerError("failed to insert booking") from e

        try:
            async with database.Booking._meta.db.transaction():
                # TODO: Add date collision check

                db_booking = (
                    await database.Booking.insert(db_booking).returning(*database.Booking.all_columns()).run()
                )[0]
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

    async def read_booking(
        self,
        actor: domain.UserID,
        booking_id: domain.BookingID,
    ) -> domain.Booking | None:
        try:
            domain_booking = await self._cache.get(self._ks.key(booking_id.hex), t=domain.Booking)
            if domain_booking is not None:
                return domain_booking

            async with database.Booking._meta.db.transaction():
                db_booking = (
                    await database.Booking.objects()
                    .where(
                        database.Booking.id == booking_id,
                        database.Booking.deleted_at.is_null(),
                    )
                    .first()
                    .run()
                )
                if db_booking is None:
                    return None

                domain_booking = projection(db_booking)

                await self._cache.set(self._ks.key(booking_id.hex), domain_booking, expire=self._cache.HOT_FEAT)

            return domain_booking
        except ProjectionError as e:
            raise errors.InternalServerError("failed to read booking") from e
        except Exception as e:
            raise errors.InternalServerError("failed to read booking") from e

    async def update_booking(
        self,
        actor: domain.UserID,
        booking_id: domain.BookingID,
        update: UpdateBooking,
    ) -> domain.Booking:
        try:
            await self._cache.invalidate(self._ks.key(booking_id.hex))

            values: dict[Column | str, Any] = {
                database.Booking.booked_since: update.booked_since,
                database.Booking.booked_till: update.booked_till,
            }

            async with database.Booking._meta.db.transaction():
                db_booking = (
                    await database.Booking.update(values)
                    .where(
                        database.Booking.id == booking_id,
                        database.Booking.deleted_at.is_null(),
                        database.Booking.user == actor,
                    )
                    .returning(*database.Booking.all_columns())
                    .run()
                )[0]

                domain_booking = projection(db_booking, cast_to=domain.Booking)

                await self._cache.set(self._ks.key(domain_booking.id.hex), domain_booking, expire=self._cache.HOT_FEAT)

            return domain_booking
        except DataError as e:
            raise errors.ConflictError("invalid data object") from e
        except IndexError as e:
            raise errors.NotFoundError("no such booking") from e
        except ProjectionError as e:
            raise errors.ValidationError("invalid booking") from e
        except Exception as e:
            raise errors.InternalServerError("failed to update booking") from e

    async def delete_booking(
        self,
        actor: domain.UserID,
        booking_id: domain.BookingID,
    ) -> domain.Booking:
        try:
            await self._cache.invalidate(self._ks.key(booking_id.hex))

            async with database.Booking._meta.db.transaction():
                db_booking = (
                    await database.Booking.update({database.Booking.deleted_at: datetime.now(UTC)})
                    .where(
                        database.Booking.id == booking_id,
                        database.Booking.deleted_at.is_null(),
                        database.Booking.user == actor,
                    )
                    .returning(*database.Booking.all_columns())
                    .run()
                )[0]

                domain_booking = projection(db_booking, cast_to=domain.Booking)

            return domain_booking
        except IndexError as e:
            raise errors.NotFoundError("no such booking found") from e
        except DataError as e:
            raise errors.ConflictError("invalid data object") from e
        except ProjectionError as e:
            raise errors.ValidationError("invalid booking") from e
        except Exception as e:
            raise errors.InternalServerError("failed to delete booking") from e

    async def filter_booking(
        self,
        actor: domain.UserID,
        filter: FilterBooking,
    ) -> list[domain.Booking]:
        try:
            query = database.Booking.objects().where(database.Booking.deleted_at.is_null())

            if filter.area_id is not None:
                query = query.where(database.Booking.area._.id == filter.area_id)

            db_bookings = await query.run()
            return [projection(db_booking) for db_booking in db_bookings]
        except ProjectionError as e:
            raise errors.InternalServerError("failed to read bookings") from e
        except Exception as e:
            raise errors.InternalServerError("failed to read bookings") from e
