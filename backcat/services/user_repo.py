from datetime import UTC, datetime
from typing import Any, Protocol

from argon2 import PasswordHasher
from asyncpg import DataError, UniqueViolationError
from piccolo.columns import Column
from pydantic import BaseModel, Field

from backcat import domain
from backcat.database import tables
from backcat.database.projector import ProjectionError, projection
from backcat.services import errors
from backcat.services.cache import Cache, Keyspace


class UpdateUser(BaseModel):
    name: str | None = Field(min_length=1, max_length=150)


class UserRepo(Protocol):
    async def create_user(self, user: domain.User) -> domain.User: ...
    async def read_user(self, user_id: domain.UserID) -> domain.User | None: ...
    async def update_user(self, user_id: domain.UserID, update: UpdateUser) -> domain.User: ...
    async def delete_user(self, user_id: domain.UserID) -> domain.User: ...


class UserRepoImpl:
    def __init__(self, cache: Cache):
        self._ks = Keyspace("camping")
        self._cache = cache
        self._password_hasher = PasswordHasher()

    async def create_user(self, user: domain.User) -> domain.User:
        try:
            password_hash = self._password_hasher.hash(user.password)
            user.password = password_hash
        except Exception as e:
            raise errors.InternalServerError("failed to hash password") from e

        try:
            db_user = projection(user)
        except ProjectionError as e:
            # projection error means that the domain model was not converted to db data
            raise errors.ValidationError("invalid user") from e
        except Exception as e:
            raise errors.InternalServerError("failed to insert user") from e

        try:
            async with tables.User._meta.db.transaction():
                db_user = (await tables.User.insert(db_user).returning(*tables.User.all_columns()).run())[0]
                domain_user = projection(db_user, cast_to=domain.User)

                await self._cache.set(self._ks.key(domain_user.id.hex), domain_user, expire=self._cache.HOT_FEAT)

                return domain_user
        except UniqueViolationError as e:
            # unique violation error means that the user already exists
            raise errors.ConflictError("user already exists") from e
        except DataError as e:
            # constraint violation error means that the user is invalid
            raise errors.ConflictError("invalid data object") from e
        except IndexError as e:
            # index error means that no row was inserted
            raise errors.InternalServerError("insertion failed") from e
        except ProjectionError as e:
            # projection error means that the db data was inserted but it was not converted to domain model
            raise errors.ConversionError("invalid user") from e
        except Exception as e:
            raise errors.InternalServerError("failed to insert user") from e

    async def read_user(self, user_id: domain.UserID) -> domain.User | None:
        try:
            domain_user = await self._cache.get(self._ks.key(user_id.hex), t=domain.User)
            if domain_user is not None:
                return domain_user

            db_user = (
                await tables.User.objects()
                .where(
                    tables.User.id == user_id,
                    tables.User.deleted_at.is_null(),
                )
                .first()
                .run()
            )
            if db_user is None:
                return None

            return projection(db_user)
        except ProjectionError as e:
            # projection error means that the db data was read but it was not converted to domain model
            raise errors.InternalServerError("failed to read user") from e
        except Exception as e:
            raise errors.InternalServerError("failed to read user") from e

    async def update_user(self, user_id: domain.UserID, update: UpdateUser) -> domain.User:
        try:
            await self._cache.invalidate(self._ks.key(user_id.hex))

            values: dict[Column | str, Any] = {}
            if "name" in update.model_fields_set and update.name is not None:
                values[tables.User.name] = update.name

            async with tables.User._meta.db.transaction():
                db_user = (
                    await tables.User.update(values)
                    .where(tables.User.id == user_id, tables.User.deleted_at.is_not_null())
                    .returning(*tables.User.all_columns())
                    .run()
                )[0]

                domain_user = projection(db_user, cast_to=domain.User)

                await self._cache.set(self._ks.key(domain_user.id.hex), domain_user, expire=self._cache.HOT_FEAT)

            return domain_user
        except DataError as e:
            # constraint violation error means that the user is invalid
            raise errors.ConflictError("invalid data object") from e
        except IndexError as e:
            # index error means that no row was updated
            raise errors.InternalServerError("update failed") from e
        except ProjectionError as e:
            # projection error means that the domain model was not converted to db data
            raise errors.ValidationError("invalid user") from e
        except Exception as e:
            raise errors.InternalServerError("failed to update user") from e

    async def delete_user(self, user_id: domain.UserID) -> domain.User:
        try:
            await self._cache.invalidate(self._ks.key(user_id.hex))

            async with tables.User._meta.db.transaction():
                db_user = (
                    await tables.User.update({tables.User.deleted_at: datetime.now(UTC)})
                    .where(tables.User.id == user_id, tables.User.deleted_at.is_null())
                    .returning(*tables.User.all_columns())
                    .run()
                )[0]

                domain_user = projection(db_user, cast_to=domain.User)

                await self._cache.set(self._ks.key(domain_user.id.hex), domain_user, expire=self._cache.HOT_FEAT)

            return domain_user
        except IndexError as e:
            # index error means that no row was updated
            raise errors.NotFoundError("no such user found") from e
        except DataError as e:
            # constraint violation error means that the user is invalid
            raise errors.ConflictError("invalid data object") from e
        except ProjectionError as e:
            # projection error means that the domain model was not converted to db data
            raise errors.ValidationError("invalid user") from e
        except Exception as e:
            raise errors.InternalServerError("failed to update user") from e
