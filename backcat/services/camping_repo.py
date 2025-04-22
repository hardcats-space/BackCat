from datetime import UTC, datetime
from typing import Any
from typing import Protocol, TypedDict, Unpack

from asyncpg import DataError, UniqueViolationError
from piccolo.columns import Column

from backcat import domain
from backcat.database import tables
from backcat.database.projector import ProjectionError, projection
from backcat.domain import Point
from backcat.services import errors
from backcat.services.cache import Cache, Keyspace


class UpdateCamping(TypedDict):
    polygon: list[Point]
    title: str
    description: str | None
    thumbnails: list[str]


class CampingRepo(Protocol):
    async def create_camping(self, camping: domain.Camping, user_id: domain.UserID) -> domain.Camping: ...
    async def read_camping(self, camping_id: domain.CampingID) -> domain.Camping | None: ...
    async def read_campings(self, user_id: domain.UserID) -> list[domain.Camping]: ...
    async def update_camping(self, camping_id: domain.CampingID, **update: Unpack[UpdateCamping]) -> domain.Camping: ...
    async def delete_camping(self, camping_id: domain.CampingID) -> domain.Camping: ...


class CampingRepoImpl:
    def __init__(self, cache: Cache):
        self._ks = Keyspace("camping")
        self._cache = cache

    async def create_camping(self, camping: domain.Camping, user_id: domain.UserID) -> domain.Camping:
        try:
            db_camping = projection(camping, user_id=user_id)
        except ProjectionError as e:
            raise errors.ValidationError("invalid camping") from e
        except Exception as e:
            raise errors.InternalServerError("failed to insert camping") from e

        try:
            async with tables.Camping._meta.db.transaction():
                db_camping = (await tables.Camping.insert(db_camping).returning(*tables.Camping.all_columns()).run())[0]
                domain_camping = projection(db_camping, cast_to=domain.Camping)

                await self._cache.set(self._ks.key(domain_camping.id.hex), domain_camping, expire=self._cache.HOT_FEAT)

                return domain_camping
        except UniqueViolationError as e:
            raise errors.ConflictError("camping already exists") from e
        except DataError as e:
            raise errors.ConflictError("invalid data object") from e
        except IndexError as e:
            raise errors.InternalServerError("insertion failed") from e
        except ProjectionError as e:
            raise errors.ConversionError("invalid camping") from e
        except Exception as e:
            raise errors.InternalServerError("failed to insert camping") from e

    async def read_camping(self, camping_id: domain.CampingID) -> domain.Camping | None:
        try:
            domain_camping = await self._cache.get(self._ks.key(camping_id.hex), t=domain.Camping)
            if domain_camping is not None:
                return domain_camping

            db_camping = (
                await tables.Camping.objects()
                .where(
                    tables.Camping.id == camping_id,
                    tables.Camping.deleted_at.is_null(),
                )
                .first()
                .run()
            )
            if db_camping is None:
                return None

            return projection(db_camping)
        except ProjectionError as e:
            raise errors.InternalServerError("failed to read camping") from e
        except Exception as e:
            raise errors.InternalServerError("failed to read camping") from e

    async def update_camping(self, camping_id: domain.CampingID, update: dict[str, Any]) -> domain.Camping:
        try:
            await self._cache.invalidate(self._ks.key(camping_id.hex))

            values: dict[Column | str, Any] = {}
            if "polygon" in update:
                values[tables.Camping.polygon] = update["polygon"]
            if "title" in update:
                values[tables.Camping.title] = update["title"]
            if "description" in update:
                values[tables.Camping.description] = update["description"]
            if "thumbnails" in update:
                values[tables.Camping.thumbnails] = update["thumbnails"]

            async with tables.Camping._meta.db.transaction():
                db_camping = (
                    await tables.Camping.update(values)
                    .where(tables.Camping.id == camping_id, tables.Camping.deleted_at.is_null())
                    .returning(*tables.Camping.all_columns())
                    .run()
                )[0]

                domain_camping = projection(db_camping, cast_to=domain.Camping)

                await self._cache.set(self._ks.key(domain_camping.id.hex), domain_camping, expire=self._cache.HOT_FEAT)

            return domain_camping
        except DataError as e:
            raise errors.ConflictError("invalid data object") from e
        except IndexError as e:
            raise errors.InternalServerError("update failed") from e
        except ProjectionError as e:
            raise errors.ValidationError("invalid camping") from e
        except Exception as e:
            raise errors.InternalServerError("failed to update camping") from e

    async def delete_camping(self, camping_id: domain.CampingID) -> domain.Camping:
        try:
            await self._cache.invalidate(self._ks.key(camping_id.hex))

            async with tables.Camping._meta.db.transaction():
                db_camping = (
                    await tables.Camping.update({tables.Camping.deleted_at: datetime.now(UTC)})
                    .where(tables.Camping.id == camping_id, tables.Camping.deleted_at.is_null())
                    .returning(*tables.Camping.all_columns())
                    .run()
                )[0]

                domain_camping = projection(db_camping, cast_to=domain.Camping)

                await self._cache.set(self._ks.key(domain_camping.id.hex), domain_camping, expire=self._cache.HOT_FEAT)

            return domain_camping
        except IndexError as e:
            raise errors.NotFoundError("no such camping found") from e
        except DataError as e:
            raise errors.ConflictError("invalid data object") from e
        except ProjectionError as e:
            raise errors.ValidationError("invalid camping") from e
        except Exception as e:
            raise errors.InternalServerError("failed to delete camping") from e
