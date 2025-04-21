from typing import Any, Protocol, TypedDict, Unpack

from asyncpg import DataError, UniqueViolationError
from piccolo.columns import Column

from backcat import domain
from backcat.database import tables
from backcat.database.projector import ProjectionError, projection
from backcat.services import errors
from backcat.services.cache import Cache, Keyspace


class UpdateArea(TypedDict):
    polygon: list[domain.Point]
    description: str | None
    price_amount: int
    price_currency: str


class AreaRepo(Protocol):
    async def create_area(self, area: domain.Area, camping_id: domain.CampingID) -> domain.Area: ...
    async def read_area(self, area_id: domain.AreaID) -> domain.Area | None: ...
    async def read_areas(self, camping_id: domain.CampingID | None) -> list[domain.Area]: ...
    async def update_area(self, area_id: domain.AreaID, **update: Unpack[UpdateArea]) -> domain.Area: ...
    async def delete_area(self, area_id: domain.AreaID) -> domain.Area: ...


class AreaRepoImpl:
    def __init__(self, cache: Cache):
        self._ks = Keyspace("area")
        self._cache = cache

    async def create_area(self, area: domain.Area, camping_id: domain.CampingID) -> domain.Area:
        try:
            db_area = projection(area, camping_id=camping_id)
        except ProjectionError as e:
            # projection error means that the domain model was not converted to db data
            raise errors.ValidationError("invalid area") from e
        except Exception as e:
            raise errors.InternalServerError("failed to insert area") from e

        try:
            async with tables.Area._meta.db.transaction():
                db_area = (await tables.Area.insert(db_area).returning(*tables.Area.all_columns()).run())[0]
                domain_area = projection(db_area, cast_to=domain.Area)

                await self._cache.set(self._ks.key(domain_area.id.hex), domain_area, expire=self._cache.HOT_FEAT)

                return domain_area
        except UniqueViolationError as e:
            # unique violation error means that the area already exists
            raise errors.ConflictError("area already exists") from e
        except DataError as e:
            # constraint violation error means that the area is invalid
            raise errors.ConflictError("invalid data object") from e
        except IndexError as e:
            # index error means that no row was inserted
            raise errors.InternalServerError("insertion failed") from e
        except ProjectionError as e:
            # projection error means that the db data was inserted but it was not converted to domain model
            raise errors.ConversionError("invalid area") from e
        except Exception as e:
            raise errors.InternalServerError("failed to insert area") from e

    async def read_area(self, area_id: domain.AreaID) -> domain.Area | None:
        try:
            domain_area = await self._cache.get(self._ks.key(area_id.hex), t=domain.Area)
            if domain_area is not None:
                return domain_area

            db_area = (
                await tables.Area.objects()
                .where(
                    tables.Area.id == area_id,
                    tables.Area.deleted_at.is_null(),
                )
                .first()
                .run()
            )
            if db_area is None:
                return None

            return projection(db_area)
        except ProjectionError as e:
            # projection error means that the db data was read but it was not converted to domain model
            raise errors.InternalServerError("failed to read area") from e
        except Exception as e:
            raise errors.InternalServerError("failed to read area") from e

    async def update_area(self, area_id: domain.AreaID, **update: Unpack[UpdateArea]) -> domain.Area:
        try:
            await self._cache.invalidate(self._ks.key(area_id.hex))

            # todo: validate update values

            values: dict[Column | str, Any] = {}
            if "polygon" in update:
                values[tables.Area.polygon] = update["polygon"]
            if "description" in update:
                values[tables.Area.description] = update["description"]
            if "price_amount" in update:
                values[tables.Area.price_amount] = update["price_amount"]
            if "price_currency" in update:
                values[tables.Area.price_currency] = update["price_currency"]

            async with tables.Area._meta.db.transaction():
                db_area = (
                    await tables.Area.update(values)
                    .where(tables.Area.id == area_id, tables.Area.deleted_at.is_not_null())
                    .returning(*tables.Area.all_columns())
                    .run()
                )[0]

                domain_area = projection(db_area, cast_to=domain.Area)

                await self._cache.set(self._ks.key(domain_area.id.hex), domain_area, expire=self._cache.HOT_FEAT)

            return domain_area
        except DataError as e:
            # constraint violation error means that the area is invalid
            raise errors.ConflictError("invalid data object") from e
        except IndexError as e:
            # index error means that no row was updated
            raise errors.InternalServerError("update failed") from e
        except ProjectionError as e:
            # projection error means that the domain model was not converted to db data
            raise errors.ValidationError("invalid area") from e
        except Exception as e:
            raise errors.InternalServerError("failed to update area") from e
