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
from backcat.services.errors import ServiceError


class UpdateBooking(BaseModel):
    booked_since: datetime | None = None
    booked_till: datetime | None = None


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
                # Lock the area to prevent overlapping bookings
                area_lock = await database.Area.objects().where(database.Area.id == area_id).lock_rows()
                if not area_lock:
                    raise errors.NotFoundError("area not found")

                # Check for date collisions
                collision = (
                    await database.Booking.objects()
                    .where(
                        database.Booking.area == area_id,
                        database.Booking.deleted_at.is_null(),
                        database.Booking.booked_since <= db_booking.booked_till,
                        database.Booking.booked_till >= db_booking.booked_since,
                    )
                    .first()
                )
                if collision:
                    raise errors.ConflictError("booking date collision detected")

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
        except ServiceError as e:
            raise e
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

            values: dict[Column | str, Any] = {}
            if "booked_since" in update.model_fields_set and update.booked_since is not None:
                values[database.Booking.booked_since] = update.booked_since
            if "booked_till" in update.model_fields_set and update.booked_till is not None:
                values[database.Booking.booked_till] = update.booked_till

            async with database.Booking._meta.db.transaction():
                # Lock the booking and area to prevent conflicts
                booking_lock = (
                    await database.Booking.objects()
                    .where(
                        database.Booking.id == booking_id,
                        database.Booking.deleted_at.is_null(),
                        database.Booking.user == actor,
                    )
                    .lock_rows()
                    .first()
                )
                if not booking_lock:
                    raise errors.NotFoundError("booking not found")

                area_lock = (
                    await database.Area.objects()
                    .where(database.Area.id == booking_lock.area)
                    .lock_rows()
                    .first()
                )
                if not area_lock:
                    raise errors.NotFoundError("area not found")

                # Check for date collisions
                collision = (
                    await database.Booking.objects()
                    .where(
                        database.Booking.area == booking_lock.area,
                        database.Booking.id != booking_id,
                        database.Booking.deleted_at.is_null(),
                        database.Booking.booked_since <= update.booked_till,
                        database.Booking.booked_till >= update.booked_since,
                    )
                    .first()
                )
                if collision:
                    raise errors.ConflictError("booking date collision detected")

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
        except ServiceError as e:
            raise e
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
