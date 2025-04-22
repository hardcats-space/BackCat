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


class UpdateReview(TypedDict):
    rating: int
    comment: str | None


class ReviewRepo(Protocol):
    async def create_review(self, review: domain.Review, area_id: domain.AreaID, user_id: domain.UserID) -> domain.Review: ...
    async def read_review(self, review_id: domain.ReviewID) -> domain.Review | None: ...
    async def read_reviews(self, area_id: domain.AreaID) -> list[domain.Review]: ...
    async def update_review(self, review_id: domain.ReviewID, **update: Unpack[UpdateReview]) -> domain.Review: ...
    async def delete_review(self, review_id: domain.ReviewID) -> domain.Review: ...


class ReviewRepoImpl:
    def __init__(self, cache: Cache):
        self._ks = Keyspace("review")
        self._cache = cache

    async def create_review(self, review: domain.Review, area_id: domain.AreaID, user_id: domain.UserID) -> domain.Review:
        try:
            db_review = projection(review, area_id=area_id, user_id=user_id)
        except ProjectionError as e:
            raise errors.ValidationError("invalid review") from e
        except Exception as e:
            raise errors.InternalServerError("failed to insert review") from e

        try:
            async with tables.Review._meta.db.transaction():
                db_review = (await tables.Review.insert(db_review).returning(*tables.Review.all_columns()).run())[0]
                domain_review = projection(db_review, cast_to=domain.Review)

                await self._cache.set(self._ks.key(domain_review.id.hex), domain_review, expire=self._cache.HOT_FEAT)

                return domain_review
        except UniqueViolationError as e:
            raise errors.ConflictError("review already exists") from e
        except DataError as e:
            raise errors.ConflictError("invalid data object") from e
        except IndexError as e:
            raise errors.InternalServerError("insertion failed") from e
        except ProjectionError as e:
            raise errors.ConversionError("invalid review") from e
        except Exception as e:
            raise errors.InternalServerError("failed to insert review") from e

    async def read_review(self, review_id: domain.ReviewID) -> domain.Review | None:
        try:
            domain_review = await self._cache.get(self._ks.key(review_id.hex), t=domain.Review)
            if domain_review is not None:
                return domain_review

            db_review = (
                await tables.Review.objects()
                .where(
                    tables.Review.id == review_id,
                    tables.Review.deleted_at.is_null(),
                )
                .first()
                .run()
            )
            if db_review is None:
                return None

            return projection(db_review)
        except ProjectionError as e:
            raise errors.InternalServerError("failed to read review") from e
        except Exception as e:
            raise errors.InternalServerError("failed to read review") from e

    async def read_reviews(self, area_id: domain.AreaID) -> list[domain.Review]:
        try:
            db_reviews = (
                await tables.Review.objects()
                .where(
                    tables.Review.area == area_id,
                    tables.Review.deleted_at.is_null(),
                )
                .run()
            )
            return [projection(db_review) for db_review in db_reviews]
        except ProjectionError as e:
            raise errors.InternalServerError("failed to read reviews") from e
        except Exception as e:
            raise errors.InternalServerError("failed to read reviews") from e

    async def update_review(self, review_id: domain.ReviewID, **update: dict[str, Any]) -> domain.Review:
        try:
            await self._cache.invalidate(self._ks.key(review_id.hex))

            values: dict[Column | str, Any] = {}
            if "rating" in update:
                values[tables.Review.rating] = update["rating"]
            if "comment" in update:
                values[tables.Review.comment] = update["comment"]

            async with tables.Review._meta.db.transaction():
                db_review = (
                    await tables.Review.update(values)
                    .where(tables.Review.id == review_id, tables.Review.deleted_at.is_null())
                    .returning(*tables.Review.all_columns())
                    .run()
                )[0]

                domain_review = projection(db_review, cast_to=domain.Review)

                await self._cache.set(self._ks.key(domain_review.id.hex), domain_review, expire=self._cache.HOT_FEAT)

            return domain_review
        except DataError as e:
            raise errors.ConflictError("invalid data object") from e
        except IndexError as e:
            raise errors.InternalServerError("update failed") from e
        except ProjectionError as e:
            raise errors.ValidationError("invalid review") from e
        except Exception as e:
            raise errors.InternalServerError("failed to update review") from e

    async def delete_review(self, review_id: domain.ReviewID) -> domain.Review:
        try:
            await self._cache.invalidate(self._ks.key(review_id.hex))

            async with tables.Review._meta.db.transaction():
                db_review = (
                    await tables.Review.update({tables.Review.deleted_at: datetime.now(UTC)})
                    .where(tables.Review.id == review_id, tables.Review.deleted_at.is_null())
                    .returning(*tables.Review.all_columns())
                    .run()
                )[0]

                domain_review = projection(db_review, cast_to=domain.Review)

                await self._cache.set(self._ks.key(domain_review.id.hex), domain_review, expire=self._cache.HOT_FEAT)

            return domain_review
        except IndexError as e:
            raise errors.NotFoundError("no such review found") from e
        except DataError as e:
            raise errors.ConflictError("invalid data object") from e
        except ProjectionError as e:
            raise errors.ValidationError("invalid review") from e
        except Exception as e:
            raise errors.InternalServerError("failed to delete review") from e