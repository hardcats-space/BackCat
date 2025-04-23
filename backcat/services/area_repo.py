from datetime import UTC, datetime
from typing import Any, Protocol

from asyncpg import DataError, UniqueViolationError
from piccolo.columns import Column
from pydantic import BaseModel, Field

from backcat import database, domain
from backcat.database.projector import ProjectionError, projection
from backcat.services import errors
from backcat.services.cache import Cache, Keyspace


class UpdateArea(BaseModel):
    polygon: list[domain.Point] | None = Field(None, min_length=3)
    description: str | None = Field(None, max_length=5000)
    price_amount: int | None = None
    price_currency: str | None = None


class FilterArea(BaseModel):
    camping_id: domain.CampingID | None = None


class AreaRepo(Protocol):
    async def create_area(
        self,
        actor: domain.UserID,
        area: domain.Area,
        camping_id: domain.CampingID,
    ) -> domain.Area: ...

    async def read_area(
        self,
        actor: domain.UserID,
        area_id: domain.AreaID,
    ) -> domain.Area | None: ...

    async def update_area(
        self,
        actor: domain.UserID,
        area_id: domain.AreaID,
        update: UpdateArea,
    ) -> domain.Area: ...

    async def delete_area(
        self,
        actor: domain.UserID,
        area_id: domain.AreaID,
    ) -> domain.Area: ...

    async def filter_area(
        self,
        actor: domain.UserID,
        filter: FilterArea,
    ) -> list[domain.Area]: ...


class AreaRepoImpl(AreaRepo):
    def __init__(self, cache: Cache):
        self._ks = Keyspace("area")
        self._cache = cache

    async def create_area(self, actor: domain.UserID, area: domain.Area, camping_id: domain.CampingID) -> domain.Area:
        try:
            db_area = projection(area, camping_id=camping_id, user_id=actor)
        except ProjectionError as e:
            # projection error means that the domain model was not converted to db data
            raise errors.ValidationError("invalid area") from e
        except Exception as e:
            raise errors.InternalServerError("failed to insert area") from e

        try:
            async with database.Area._meta.db.transaction():
                db_area = (await database.Area.insert(db_area).returning(*database.Area.all_columns()).run())[0]
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

    async def read_area(self, actor: domain.UserID, area_id: domain.AreaID) -> domain.Area | None:
        try:
            domain_area = await self._cache.get(self._ks.key(area_id.hex), t=domain.Area)
            if domain_area is not None:
                return domain_area

            async with database.Camping._meta.db.transaction():
                db_area = (
                    await database.Area.objects()
                    .where(
                        database.Area.id == area_id,
                        database.Area.deleted_at.is_null(),
                    )
                    .first()
                    .run()
                )
                if db_area is None:
                    return None

                domain_area = projection(db_area)

                await self._cache.set(self._ks.key(area_id.hex), domain_area, expire=self._cache.HOT_FEAT)

            return domain_area
        except ProjectionError as e:
            # projection error means that the db data was read but it was not converted to domain model
            raise errors.InternalServerError("failed to read area") from e
        except Exception as e:
            raise errors.InternalServerError("failed to read area") from e

    async def update_area(self, actor: domain.UserID, area_id: domain.AreaID, update: UpdateArea) -> domain.Area:
        try:
            await self._cache.invalidate(self._ks.key(area_id.hex))

            values: dict[Column | str, Any] = {}
            if "polygon" in update.model_fields_set and update.polygon is not None:
                values[database.Area.polygon] = update.polygon
            if "description" in update.model_fields_set:  # nullable field, no check for None
                values[database.Area.description] = update.description
            if "price_amount" in update.model_fields_set and update.price_amount is not None:
                values[database.Area.price_amount] = update.price_amount
            if "price_currency" in update.model_fields_set and update.price_currency is not None:
                values[database.Area.price_currency] = update.price_currency

            async with database.Area._meta.db.transaction():
                db_area = (
                    await database.Area.update(values)
                    .where(
                        database.Area.id == area_id,
                        database.Area.deleted_at.is_null(),
                        database.Area.user == actor,
                    )
                    .returning(*database.Area.all_columns())
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
            raise errors.NotFoundError("no such area") from e
        except ProjectionError as e:
            # projection error means that the domain model was not converted to db data
            raise errors.ValidationError("invalid area") from e
        except Exception as e:
            raise errors.InternalServerError("failed to update area") from e

    async def delete_area(self, actor: domain.UserID, area_id: domain.AreaID) -> domain.Area:
        try:
            await self._cache.invalidate(self._ks.key(area_id.hex))

            async with database.Area._meta.db.transaction():
                db_area = (
                    await database.Area.update({database.Area.deleted_at: datetime.now(UTC)})
                    .where(
                        database.Area.id == area_id,
                        database.Area.deleted_at.is_null(),
                        database.Area.user == actor,
                    )
                    .returning(*database.Area.all_columns())
                    .run()
                )[0]

                domain_area = projection(db_area, cast_to=domain.Area)

            return domain_area
        except IndexError as e:
            # index error means that no row was updated
            raise errors.NotFoundError("no such area found") from e
        except DataError as e:
            # constraint violation error means that the area is invalid
            raise errors.ConflictError("invalid data object") from e
        except ProjectionError as e:
            # projection error means that the domain model was not converted to db data
            raise errors.ValidationError("invalid area") from e
        except Exception as e:
            raise errors.InternalServerError("failed to update area") from e

    async def filter_area(
        self,
        actor: domain.UserID,
        filter: FilterArea,
    ) -> list[domain.Area]:
        try:
            query = database.Area.objects().where(database.Area.deleted_at.is_null())

            if filter.camping_id is not None:
                query = query.where(database.Area.camping._.id == filter.camping_id)

            db_areas = await query.run()
            return [projection(db_area) for db_area in db_areas]
        except ProjectionError as e:
            # projection error means that the db data was read but it was not converted to domain model
            raise errors.InternalServerError("failed to read area") from e
        except Exception as e:
            raise errors.InternalServerError("failed to read area") from e
