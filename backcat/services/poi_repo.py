from datetime import UTC, datetime
from typing import Any, Protocol

from asyncpg import DataError, UniqueViolationError
from piccolo.columns import Column
from pydantic import BaseModel

from backcat import database
from backcat import domain
from backcat.database.projector import ProjectionError, projection
from backcat.services import errors
from backcat.services.cache import Cache, Keyspace


class UpdatePOI(BaseModel):
    kind: domain.POIKind | None = None
    point: domain.Point | None = None
    name: str | None = None
    description: str | None = None


class FilterPOI(BaseModel):
    camping_id: domain.CampingID | None = None


class POIRepo(Protocol):
    async def create_poi(
        self,
        actor: domain.UserID,
        poi: domain.POI,
        camping_id: domain.CampingID,
    ) -> domain.POI: ...

    async def read_poi(
        self,
        actor: domain.UserID,
        poi_id: domain.POIID,
    ) -> domain.POI | None: ...

    async def update_poi(
        self,
        actor: domain.UserID,
        poi_id: domain.POIID,
        update: UpdatePOI,
    ) -> domain.POI: ...

    async def delete_poi(
        self,
        actor: domain.UserID,
        poi_id: domain.POIID,
    ) -> domain.POI: ...

    async def filter_poi(
        self,
        actor: domain.UserID,
        filter: FilterPOI,
    ) -> list[domain.POI]: ...


class POIRepoImpl(POIRepo):
    def __init__(self, cache: Cache):
        self._ks = Keyspace("poi")
        self._cache = cache

    async def create_poi(self, actor: domain.UserID, poi: domain.POI, camping_id: domain.CampingID) -> domain.POI:
        try:
            db_poi = projection(poi, camping_id=camping_id, user_id=actor)
        except ProjectionError as e:
            # projection error means that the domain model was not converted to db data
            raise errors.ValidationError("invalid POI") from e
        except Exception as e:
            raise errors.InternalServerError("failed to insert POI") from e

        try:
            async with database.POI._meta.db.transaction():
                db_poi = (await database.POI.insert(db_poi).returning(*database.POI.all_columns()).run())[0]
                domain_poi = projection(db_poi, cast_to=domain.POI)

                await self._cache.set(self._ks.key(domain_poi.id.hex), domain_poi, expire=self._cache.HOT_FEAT)

                return domain_poi
        except UniqueViolationError as e:
            # unique violation error means that the poi already exists
            raise errors.ConflictError("POI already exists") from e
        except DataError as e:
            # constraint violation error means that the poi is invalid
            raise errors.ConflictError("invalid data object") from e
        except IndexError as e:
            # index error means that no row was inserted
            raise errors.InternalServerError("insertion failed") from e
        except ProjectionError as e:
            # projection error means that the db data was inserted but it was not converted to domain model
            raise errors.ConversionError("invalid POI") from e
        except Exception as e:
            raise errors.InternalServerError("failed to insert POI") from e

    async def read_poi(self, actor: domain.UserID, poi_id: domain.POIID) -> domain.POI | None:
        try:
            domain_poi = await self._cache.get(self._ks.key(poi_id.hex), t=domain.POI)
            if domain_poi is not None:
                return domain_poi

            async with database.POI._meta.db.transaction():
                db_poi = (
                    await database.POI.objects()
                    .where(
                        database.POI.id == poi_id,
                        database.POI.deleted_at.is_null(),
                    )
                    .first()
                    .run()
                )
                if db_poi is None:
                    return None

                domain_poi = projection(db_poi)

                await self._cache.set(self._ks.key(poi_id.hex), domain_poi, expire=self._cache.HOT_FEAT)

            return domain_poi
        except ProjectionError as e:
            # projection error means that the db data was read, but it was not converted to a domain model
            raise errors.InternalServerError("failed to read POI") from e
        except Exception as e:
            raise errors.InternalServerError("failed to read POI") from e

    async def update_poi(self, actor: domain.UserID, poi_id: domain.POIID, update: UpdatePOI) -> domain.POI:
        try:
            await self._cache.invalidate(self._ks.key(poi_id.hex))

            values: dict[Column | str, Any] = {}
            if "kind" in update.model_fields_set and update.kind is not None:
                values[database.POI.kind] = update.kind
            if "point" in update.model_fields_set and update.point is not None:
                values[database.POI.lat] = update.point.lat
                values[database.POI.lon] = update.point.lon
            if "name" in update.model_fields_set and update.name is not None:
                values[database.POI.name] = update.name
            if "description" in update.model_fields_set:  # nullable field, no check for None
                values[database.POI.description] = update.description

            async with database.POI._meta.db.transaction():
                db_poi = (
                    await database.POI.update(values)
                    .where(
                        database.POI.id == poi_id,
                        database.POI.deleted_at.is_null(),
                        database.POI.user == actor,
                    )
                    .returning(*database.POI.all_columns())
                    .run()
                )[0]

                domain_poi = projection(db_poi, cast_to=domain.POI)

                await self._cache.set(self._ks.key(domain_poi.id.hex), domain_poi, expire=self._cache.HOT_FEAT)

            return domain_poi
        except DataError as e:
            # constraint violation error means that the poi is invalid
            raise errors.ConflictError("invalid data object") from e
        except IndexError as e:
            # index error means that no row was updated
            raise errors.NotFoundError("no such POI") from e
        except ProjectionError as e:
            # projection error means that the domain model was not converted to db data
            raise errors.ValidationError("invalid POI") from e
        except Exception as e:
            raise errors.InternalServerError("failed to update POI") from e

    async def delete_poi(self, actor: domain.UserID, poi_id: domain.POIID) -> domain.POI:
        try:
            await self._cache.invalidate(self._ks.key(poi_id.hex))

            async with database.POI._meta.db.transaction():
                db_poi = (
                    await database.POI.update({database.POI.deleted_at: datetime.now(UTC)})
                    .where(
                        database.POI.id == poi_id,
                        database.POI.deleted_at.is_null(),
                        database.POI.user == actor,
                    )
                    .returning(*database.POI.all_columns())
                    .run()
                )[0]

                domain_poi = projection(db_poi, cast_to=domain.POI)

            return domain_poi
        except IndexError as e:
            # index error means that no row was updated
            raise errors.NotFoundError("no such POI found") from e
        except DataError as e:
            # constraint violation error means that the poi is invalid
            raise errors.ConflictError("invalid data object") from e
        except ProjectionError as e:
            # projection error means that the domain model was not converted to db data
            raise errors.ValidationError("invalid POI") from e
        except Exception as e:
            raise errors.InternalServerError("failed to delete POI") from e

    async def filter_poi(
        self,
        actor: domain.UserID,
        filter: FilterPOI,
    ) -> list[domain.POI]:
        try:
            query = database.POI.objects().where(database.POI.deleted_at.is_null())

            if filter.camping_id is not None:
                query = query.where(database.POI.camping._.id == filter.camping_id)

            db_pois = await query.run()
            return [projection(db_poi) for db_poi in db_pois]
        except ProjectionError as e:
            # projection error means that the db data was read, but it was not converted to a domain model
            raise errors.InternalServerError("failed to read POI") from e
        except Exception as e:
            raise errors.InternalServerError("failed to read POI") from e
