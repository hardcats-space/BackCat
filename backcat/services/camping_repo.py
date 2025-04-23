from datetime import UTC, datetime
from typing import Any, Protocol, override

from asyncpg import DataError, UniqueViolationError
from piccolo.columns import Column
from pydantic import BaseModel, Field

from backcat import database, domain
from backcat.domain import Point
from backcat.services import errors
from backcat.services.cache import Cache, Keyspace


class UpdateCamping(BaseModel):
    polygon: list[Point] | None = Field(None, min_length=3)
    title: str | None = Field(None, max_length=250)
    description: str | None = Field(None, max_length=5000)
    thumbnails: list[str] | None = Field(None, min_length=0, max_length=5)


class FilterCamping(BaseModel, frozen=True):
    user_id: domain.UserID | None = None
    booked: bool | None = None


class CampingRepo(Protocol):
    async def create_camping(
        self,
        actor: domain.UserID,
        camping: domain.Camping,
    ) -> domain.Camping: ...

    async def read_camping(
        self,
        actor: domain.UserID,
        camping_id: domain.CampingID,
    ) -> domain.Camping | None: ...

    async def filter_camping(
        self,
        actor: domain.UserID,
        filter: FilterCamping,
    ) -> list[domain.Camping]: ...

    async def update_camping(
        self,
        actor: domain.UserID,
        camping_id: domain.CampingID,
        update: UpdateCamping,
    ) -> domain.Camping: ...

    async def delete_camping(
        self,
        actor: domain.UserID,
        camping_id: domain.CampingID,
    ) -> domain.Camping: ...


class CampingRepoImpl(CampingRepo):
    def __init__(self, cache: Cache):
        self._ks = Keyspace("camping")
        self._cache = cache

    @override
    async def create_camping(
        self,
        actor: domain.UserID,
        camping: domain.Camping,
    ) -> domain.Camping:
        try:
            db_camping = database.projection(camping, user_id=actor)
        except database.ProjectionError as e:
            # projection error means that the domain model was not converted to db data
            raise errors.ValidationError("invalid camping") from e
        except Exception as e:
            raise errors.InternalServerError("failed to insert camping") from e

        try:
            async with database.Camping._meta.db.transaction():
                db_camping = (
                    await database.Camping.insert(db_camping).returning(*database.Camping.all_columns()).run()
                )[0]
                domain_camping = database.projection(db_camping, cast_to=domain.Camping)
                await self._cache.set(self._ks.key(domain_camping.id.hex), domain_camping, expire=self._cache.HOT_FEAT)
                return domain_camping
        except UniqueViolationError as e:
            # unique violation error means that the camping already exists
            raise errors.ConflictError("camping already exists") from e
        except DataError as e:
            # constraint violation error means that the camping is invalid
            raise errors.ConflictError("invalid data object") from e
        except IndexError as e:
            # index error means that no row was inserted
            raise errors.InternalServerError("insertion failed") from e
        except database.ProjectionError as e:
            # projection error means that the db data was inserted but it was not converted to domain model
            raise errors.ConversionError("invalid camping") from e
        except Exception as e:
            raise errors.InternalServerError("failed to insert camping") from e

    @override
    async def read_camping(
        self,
        actor: domain.UserID,
        camping_id: domain.CampingID,
    ) -> domain.Camping | None:
        try:
            domain_camping = await self._cache.get(self._ks.key(camping_id.hex), t=domain.Camping)
            if domain_camping is not None:
                return domain_camping
            db_camping = (
                await database.Camping.objects()
                .where(
                    database.Camping.id == camping_id,
                    database.Camping.deleted_at.is_null(),
                )
                .first()
                .run()
            )
            if db_camping is None:
                return None

            return database.projection(db_camping)
        except database.ProjectionError as e:
            # projection error means that the db data was read but it was not converted to domain model
            raise errors.InternalServerError("failed to read camping") from e
        except Exception as e:
            raise errors.InternalServerError("failed to read camping") from e

    @override
    async def update_camping(
        self,
        actor: domain.UserID,
        camping_id: domain.CampingID,
        update: UpdateCamping,
    ) -> domain.Camping:
        try:
            await self._cache.invalidate(self._ks.key(camping_id.hex))

            values: dict[Column | str, Any] = {}
            if "polygon" in update.model_fields_set and update.polygon is not None:
                values[database.Camping.polygon] = update.polygon
            if "title" in update.model_fields_set and update.title is not None:
                values[database.Camping.title] = update.title
            if "description" in update.model_fields_set and update.description is not None:
                values[database.Camping.description] = update.description
            if "thumbnails" in update.model_fields_set and update.thumbnails is not None:
                values[database.Camping.thumbnails] = update.thumbnails

            async with database.Camping._meta.db.transaction():
                db_camping = (
                    await database.Camping.update(values)
                    .where(
                        database.Camping.id == camping_id,
                        database.Camping.user._.id == actor,
                        database.Camping.deleted_at.is_null(),
                    )
                    .returning(*database.Camping.all_columns())
                    .run()
                )[0]

                domain_camping = database.projection(db_camping, cast_to=domain.Camping)

                await self._cache.set(self._ks.key(domain_camping.id.hex), domain_camping, expire=self._cache.HOT_FEAT)

            return domain_camping
        except DataError as e:
            # constraint violation error means that the camping is invalid
            raise errors.ConflictError("invalid data object") from e
        except IndexError as e:
            # index error means that no row was updated
            raise errors.InternalServerError("update failed") from e
        except database.ProjectionError as e:
            # projection error means that the domain model was not converted to db data
            raise errors.ValidationError("invalid camping") from e
        except Exception as e:
            raise errors.InternalServerError("failed to update camping") from e

    @override
    async def delete_camping(
        self,
        actor: domain.UserID,
        camping_id: domain.CampingID,
    ) -> domain.Camping:
        try:
            await self._cache.invalidate(self._ks.key(camping_id.hex))

            async with database.Camping._meta.db.transaction():
                db_camping = (
                    await database.Camping.update({database.Camping.deleted_at: datetime.now(UTC)})
                    .where(
                        database.Camping.id == camping_id,
                        database.Camping.user._.id == actor,
                        database.Camping.deleted_at.is_null(),
                    )
                    .returning(*database.Camping.all_columns())
                    .run()
                )[0]

                domain_camping = database.projection(db_camping, cast_to=domain.Camping)

                await self._cache.set(self._ks.key(domain_camping.id.hex), domain_camping, expire=self._cache.HOT_FEAT)

            return domain_camping
        except IndexError as e:
            # index error means that no row was updated
            raise errors.NotFoundError("no such camping found") from e
        except DataError as e:
            # constraint violation error means that the camping is invalid
            raise errors.ConflictError("invalid data object") from e
        except database.ProjectionError as e:
            # projection error means that the domain model was not converted to db data
            raise errors.ValidationError("invalid camping") from e
        except Exception as e:
            raise errors.InternalServerError("failed to update camping") from e

    @override
    async def filter_camping(
        self,
        actor: domain.UserID,
        filter: FilterCamping,
    ) -> list[domain.Camping]:
        try:
            cache_data: dict[str, list[domain.Camping]] | None = await self._cache.get(self._ks.key(str(hash(filter))))
            if cache_data is not None and "campings" in cache_data:
                return cache_data["campings"]

            query = database.Camping.objects().where(database.Camping.deleted_at.is_null())

            if filter.user_id is not None:
                query = query.where(database.Camping.user == filter.user_id)

            if filter.booked is not None and filter.booked:
                # todo: rewrite using piccolo query builder
                query = database.Camping.raw(f"""
                    select c.*
                    from {database.Camping._meta.tablename} c
                    left join {database.Area._meta.tablename} a
                        on a.{database.Area.camping._meta.db_column_name} = c.{database.Camping.id._meta.db_column_name}   
                    left join {database.Booking._meta.tablename} b
                        on b.{database.Booking.area._meta.db_column_name} = a.{database.Area.id._meta.db_column_name} 
                    where
                        b.{database.Booking.user._meta.db_column_name} = '{actor}'::uuid
                        and b.{database.Booking.deleted_at._meta.db_column_name} is null
                        and a.{database.Area.deleted_at._meta.db_column_name} is null
                        and c.{database.Camping.deleted_at._meta.db_column_name} is null
                """)

            if filter.booked is not None and not filter.booked:
                # todo: rewrite using piccolo query builder
                query = database.Camping.raw(f"""
                    select c.*
                    from {database.Camping._meta.tablename} c
                    left join {database.Area._meta.tablename} a
                        on a.{database.Area.camping._meta.db_column_name} = c.{database.Camping.id._meta.db_column_name}   
                    left join {database.Booking._meta.tablename} b
                        on b.{database.Booking.area._meta.db_column_name} = a.{database.Area.id._meta.db_column_name} 
                    where
                        b is null or (
                            b.{database.Booking.user._meta.db_column_name} <> '{actor}'::uuid
                            and b.{database.Booking.deleted_at._meta.db_column_name} is null
                            and a.{database.Area.deleted_at._meta.db_column_name} is null
                            and c.{database.Camping.deleted_at._meta.db_column_name} is null
                        )
                """)

            db_campings = await query.run()
            domain_campings = [database.projection(camping, cast_to=domain.Camping) for camping in db_campings]  # type: ignore

            await self._cache.set(
                self._ks.key(str(hash(filter))), {"campings": domain_campings}, expire=self._cache.LIVE_FEAT
            )

            return domain_campings
        except database.ProjectionError as e:
            # projection error means that the db data was read but it was not converted to domain model
            raise errors.InternalServerError("failed to read camping") from e
        except Exception as e:
            raise errors.InternalServerError("failed to read camping") from e
