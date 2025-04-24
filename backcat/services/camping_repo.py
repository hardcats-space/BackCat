from datetime import UTC, datetime
from pathlib import Path
from textwrap import dedent
from typing import Any, Protocol, override
from uuid import uuid4

from asyncpg import DataError, UniqueViolationError
from piccolo.columns import Column
from pydantic import BaseModel, Field

from backcat import database, domain
from backcat.domain import Point
from backcat.services import errors
from backcat.services.cache import Cache, Keyspace
from backcat.services.filestorage import FileStorage


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

    async def add_thumbnail(
        self,
        actor: domain.UserID,
        camping_id: domain.CampingID,
        thumbnail: str,
    ) -> domain.Camping: ...

    async def upload_thumbnail(
        self,
        actor: domain.UserID,
        camping_id: domain.CampingID,
        thumbnail: bytes,
    ) -> domain.Camping: ...

    async def remove_thumbnail(
        self,
        actor: domain.UserID,
        camping_id: domain.CampingID,
        thumbnail_index: int,
    ) -> domain.Camping: ...


class CampingRepoImpl(CampingRepo):
    def __init__(self, cache: Cache, file_storage: FileStorage):
        self._ks = Keyspace("camping")
        self._cache = cache
        self._fs = file_storage

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
                values[database.Camping.polygon] = [[point.lat, point.lon] for point in update.polygon]
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
                        database.Camping.user == actor,
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
            raise errors.NotFoundError("no such camping found") from e
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
                        database.Camping.user == actor,
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
                query = database.Camping.raw(
                    dedent(f"""
                    with booked as (
                        select
                            b.{database.Booking.id._meta.db_column_name} as id,
                            b.{database.Booking.user._meta.db_column_name} as user,
                            b.{database.Booking.area._meta.db_column_name} as area
                        from {database.Booking._meta.tablename} b
                        where
                            b.{database.Booking.user._meta.db_column_name} = '{filter.user_id or actor}'::uuid
                            and b.{database.Booking.deleted_at._meta.db_column_name} is null
                    ), booked_areas as (
                        select
                            a.{database.Area.id._meta.db_column_name} as id,
                            a.{database.Area.camping._meta.db_column_name} as camping
                        from {database.Area._meta.tablename} a
                        inner join booked b on b.area = a.{database.Area.id._meta.db_column_name}
                        where a.{database.Area.deleted_at._meta.db_column_name} is null
                    )
                    select c.*
                    from {database.Camping._meta.tablename} c
                    inner join booked_areas a on a.camping = c.{database.Camping.id._meta.db_column_name}
                    where {database.Camping.deleted_at._meta.db_column_name} is null;
                """),
                )

            if filter.booked is not None and not filter.booked:
                query = database.Camping.raw(
                    dedent(f"""
                    with not_booked as (
                        select
                            b.{database.Booking.id._meta.db_column_name} as id,
                            b.{database.Booking.user._meta.db_column_name} as user,
                            b.{database.Booking.area._meta.db_column_name} as area
                        from {database.Booking._meta.tablename} b
                        where
                            b.{database.Booking.user._meta.db_column_name} <> '{actor}'::uuid
                            or b.{database.Booking.deleted_at._meta.db_column_name} is not null
                    ), not_booked_areas as (
                        select
                            a.{database.Area.id._meta.db_column_name} as id,
                            a.{database.Area.camping._meta.db_column_name} as camping
                        from {database.Area._meta.tablename} a
                        inner join not_booked b
                            on b.area = a.{database.Area.id._meta.db_column_name}
                    )
                    select c.*
                    from {database.Camping._meta.tablename} c
                    inner not_booked_areas a on a.camping = c.{database.Camping.id._meta.db_column_name}   
                    where {database.Camping.deleted_at._meta.db_column_name} is null
                """)
                )

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

    @override
    async def add_thumbnail(
        self,
        actor: domain.UserID,
        camping_id: domain.CampingID,
        thumbnail: str,
    ) -> domain.Camping:
        try:
            await self._cache.invalidate(self._ks.key(camping_id.hex))

            async with database.Camping._meta.db.transaction():
                camping: database.Camping | None = (
                    await database.Camping.objects()
                    .where(
                        database.Camping.id == camping_id,
                        database.Camping.user == actor,
                        database.Camping.deleted_at.is_null(),
                    )
                    .first()
                    .lock_rows()
                )  # type: ignore
                if camping is None:
                    raise errors.NotFoundError("no such camping found")

                if len(camping.thumbnails) >= 5:
                    raise errors.ConflictError("too many thumbnails")

                db_camping = (
                    await database.Camping.update({
                        database.Camping.thumbnails: database.Camping.thumbnails + [thumbnail]
                    })
                    .where(
                        database.Camping.id == camping_id,
                        database.Camping.user == actor,
                        database.Camping.deleted_at.is_null(),
                    )
                    .returning(*database.Camping.all_columns())
                    .run()
                )[0]

                domain_camping = database.projection(db_camping, cast_to=domain.Camping)

                await self._cache.set(self._ks.key(domain_camping.id.hex), domain_camping, expire=self._cache.HOT_FEAT)

            return domain_camping
        except errors.ServiceError as e:
            raise e from e
        except IndexError as e:
            # index error means that no row was updated
            raise errors.NotFoundError("no such camping found") from e
        except database.ProjectionError as e:
            # projection error means that the domain model was not converted to db data
            raise errors.ValidationError("invalid camping") from e
        except Exception as e:
            raise errors.InternalServerError("failed to update camping") from e

    @override
    async def upload_thumbnail(
        self,
        actor: domain.UserID,
        camping_id: domain.CampingID,
        thumbnail: bytes,
    ) -> domain.Camping:
        try:
            await self._cache.invalidate(self._ks.key(camping_id.hex))

            async with database.Camping._meta.db.transaction():
                camping: database.Camping | None = (
                    await database.Camping.objects()
                    .where(
                        database.Camping.id == camping_id,
                        database.Camping.user == actor,
                        database.Camping.deleted_at.is_null(),
                    )
                    .first()
                    .lock_rows()
                )  # type: ignore
                if camping is None:
                    raise errors.NotFoundError("no such camping found")

                if len(camping.thumbnails) >= 5:
                    raise errors.ConflictError("too many thumbnails")

                filepath = Path("campings") / camping_id.hex / uuid4().hex
                await self._fs.upload(filepath, thumbnail)

                thumbnail_url = await self._fs.get_url(filepath)

                db_camping = (
                    await database.Camping.update({
                        database.Camping.thumbnails: database.Camping.thumbnails + [thumbnail_url]
                    })
                    .where(
                        database.Camping.id == camping_id,
                        database.Camping.user == actor,
                        database.Camping.deleted_at.is_null(),
                    )
                    .returning(*database.Camping.all_columns())
                    .run()
                )[0]

                domain_camping = database.projection(db_camping, cast_to=domain.Camping)

                await self._cache.set(self._ks.key(domain_camping.id.hex), domain_camping, expire=self._cache.HOT_FEAT)

            return domain_camping
        except errors.ServiceError as e:
            raise e from e
        except IndexError as e:
            # index error means that no row was updated
            raise errors.NotFoundError("no such camping found") from e
        except database.ProjectionError as e:
            # projection error means that the domain model was not converted to db data
            raise errors.ValidationError("invalid camping") from e
        except Exception as e:
            raise errors.InternalServerError("failed to update camping") from e

    @override
    async def remove_thumbnail(
        self,
        actor: domain.UserID,
        camping_id: domain.CampingID,
        thumbnail_index: int,
    ) -> domain.Camping:
        if thumbnail_index < 0:
            raise errors.ValidationError("invalid thumbnail index")
        if thumbnail_index >= 5:
            raise errors.ValidationError("invalid thumbnail index")

        try:
            await self._cache.invalidate(self._ks.key(camping_id.hex))

            async with database.Camping._meta.db.transaction():
                camping: database.Camping | None = (
                    await database.Camping.objects()
                    .where(
                        database.Camping.id == camping_id,
                        database.Camping.user == actor,
                        database.Camping.deleted_at.is_null(),
                    )
                    .first()
                    .lock_rows()
                )  # type: ignore
                if camping is None:
                    raise errors.NotFoundError("no such camping found")

                if len(camping.thumbnails) >= thumbnail_index:
                    camping.thumbnails.pop(thumbnail_index)
                else:
                    raise errors.NotFoundError("no such thumbnail found")

                db_camping = (
                    await database.Camping.update({database.Camping.thumbnails: camping.thumbnails})
                    .where(
                        database.Camping.id == camping_id,
                        database.Camping.user == actor,
                        database.Camping.deleted_at.is_null(),
                    )
                    .returning(*database.Camping.all_columns())
                    .run()
                )[0]

                domain_camping = database.projection(db_camping, cast_to=domain.Camping)

                await self._cache.set(self._ks.key(domain_camping.id.hex), domain_camping, expire=self._cache.HOT_FEAT)

            return domain_camping
        except errors.ServiceError as e:
            raise e from e
        except IndexError as e:
            # index error means that no row was updated
            raise errors.NotFoundError("no such camping found") from e
        except database.ProjectionError as e:
            # projection error means that the domain model was not converted to db data
            raise errors.ValidationError("invalid camping") from e
        except Exception as e:
            raise errors.InternalServerError("failed to update camping") from e
