from typing import Protocol

from asyncpg import DataError, UniqueViolationError

from backcat import domain
from backcat.database import tables
from backcat.database.projector import ProjectionError, projection
from backcat.services import errors


class AreaRepo(Protocol):
    async def create_area(self, area: domain.Area, camping_id: domain.CampingID) -> domain.Area: ...
    async def read_area(self, area_id: domain.AreaID) -> domain.Area: ...
    async def update_area(self, area_id: domain.AreaID) -> domain.Area: ...
    async def delete_area(self, area_id: domain.AreaID) -> domain.Area: ...


class AreaRepoImpl:
    def __init__(self): ...

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
                db_area = (
                    await tables.Area.insert(projection(area, camping_id=camping_id))
                    .returning(*tables.Area.all_columns())
                    .run()
                )[0]
                return projection(db_area, cast_to=domain.Area)
        except UniqueViolationError as e:  # todo: is this the right exception?
            # unique violation error means that the area already exists
            raise errors.ConflictError("area already exists") from e
        except DataError as e:  # todo: is this the right exception?
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
