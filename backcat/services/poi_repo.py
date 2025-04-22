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


class UpdatePOI(TypedDict):
    kind: domain.POIKind
    point: domain.Point
    name: str
    description: str | None


class POIRepo(Protocol):
    async def create_poi(self, poi: domain.POI, camping_id: domain.CampingID) -> domain.POI: ...
    async def read_poi(self, poi_id: domain.POIID) -> domain.POI | None: ...
    async def read_pois(self, camping_id: domain.CampingID) -> list[domain.POI]: ...
    async def update_poi(self, poi_id: domain.POIID, **update: Unpack[UpdatePOI]) -> domain.POI: ...
    async def delete_poi(self, poi_id: domain.POIID) -> domain.POI: ...


class POIRepoImpl:
    def __init__(self, cache: Cache):
        self._ks = Keyspace("poi")
        self._cache = cache

    async def create_poi(self, poi: domain.POI, camping_id: domain.CampingID) -> domain.POI:
        try:
            db_poi = projection(poi, camping_id=camping_id)
        except ProjectionError as e:
            raise errors.ValidationError("invalid POI") from e
        except Exception as e:
            raise errors.InternalServerError("failed to insert POI") from e

        try:
            async with tables.POI._meta.db.transaction():
                db_poi = (await tables.POI.insert(db_poi).returning(*tables.POI.all_columns()).run())[0]
                domain_poi = projection(db_poi, cast_to=domain.POI)

                await self._cache.set(self._ks.key(domain_poi.id.hex), domain_poi, expire=self._cache.HOT_FEAT)

                return domain_poi
        except UniqueViolationError as e:
            raise errors.ConflictError("POI already exists") from e
        except DataError as e:
            raise errors.ConflictError("invalid data object") from e
        except IndexError as e:
            raise errors.InternalServerError("insertion failed") from e
        except ProjectionError as e:
            raise errors.ConversionError("invalid POI") from e
        except Exception as e:
            raise errors.InternalServerError("failed to insert POI") from e

    async def read_poi(self, poi_id: domain.POIID) -> domain.POI | None:
        try:
            domain_poi = await self._cache.get(self._ks.key(poi_id.hex), t=domain.POI)
            if domain_poi is not None:
                return domain_poi

            db_poi = (
                await tables.POI.objects()
                .where(
                    tables.POI.id == poi_id,
                    tables.POI.deleted_at.is_null(),
                )
                .first()
                .run()
            )
            if db_poi is None:
                return None

            return projection(db_poi)
        except ProjectionError as e:
            raise errors.InternalServerError("failed to read POI") from e
        except Exception as e:
            raise errors.InternalServerError("failed to read POI") from e

    async def read_pois(self, camping_id: domain.CampingID) -> list[domain.POI]:
        try:
            db_pois = (
                await tables.POI.objects()
                .where(
                    tables.POI.camping == camping_id,
                    tables.POI.deleted_at.is_null(),
                )
                .run()
            )
            return [projection(db_poi) for db_poi in db_pois]
        except ProjectionError as e:
            raise errors.InternalServerError("failed to read POIs") from e
        except Exception as e:
            raise errors.InternalServerError("failed to read POIs") from e

    async def update_poi(self, poi_id: domain.POIID, **update: dict[str, Any]) -> domain.POI:
        try:
            await self._cache.invalidate(self._ks.key(poi_id.hex))

            values: dict[Column | str, Any] = {}
            if "kind" in update:
                values[tables.POI.kind] = update["kind"]
            if "point" in update:
                values[tables.POI.lat] = update["point"].lat
                values[tables.POI.lon] = update["point"].lon
            if "name" in update:
                values[tables.POI.name] = update["name"]
            if "description" in update:
                values[tables.POI.description] = update["description"]

            async with tables.POI._meta.db.transaction():
                db_poi = (
                    await tables.POI.update(values)
                    .where(tables.POI.id == poi_id, tables.POI.deleted_at.is_null())
                    .returning(*tables.POI.all_columns())
                    .run()
                )[0]

                domain_poi = projection(db_poi, cast_to=domain.POI)

                await self._cache.set(self._ks.key(domain_poi.id.hex), domain_poi, expire=self._cache.HOT_FEAT)

            return domain_poi
        except DataError as e:
            raise errors.ConflictError("invalid data object") from e
        except IndexError as e:
            raise errors.InternalServerError("update failed") from e
        except ProjectionError as e:
            raise errors.ValidationError("invalid POI") from e
        except Exception as e:
            raise errors.InternalServerError("failed to update POI") from e

    async def delete_poi(self, poi_id: domain.POIID) -> domain.POI:
        try:
            await self._cache.invalidate(self._ks.key(poi_id.hex))

            async with tables.POI._meta.db.transaction():
                db_poi = (
                    await tables.POI.update({tables.POI.deleted_at: datetime.now(UTC)})
                    .where(tables.POI.id == poi_id, tables.POI.deleted_at.is_null())
                    .returning(*tables.POI.all_columns())
                    .run()
                )[0]

                domain_poi = projection(db_poi, cast_to=domain.POI)

                await self._cache.set(self._ks.key(domain_poi.id.hex), domain_poi, expire=self._cache.HOT_FEAT)

            return domain_poi
        except IndexError as e:
            raise errors.NotFoundError("no such POI found") from e
        except DataError as e:
            raise errors.ConflictError("invalid data object") from e
        except ProjectionError as e:
            raise errors.ValidationError("invalid POI") from e
        except Exception as e:
            raise errors.InternalServerError("failed to delete POI") from e
