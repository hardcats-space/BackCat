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


class UpdateReview(BaseModel):
    rating: int | None = None
    comment: str | None = None


class FilterReview(BaseModel):
    area_id: domain.AreaID | None


class ReviewRepo(Protocol):
    async def create_review(
        self,
        actor: domain.UserID,
        review: domain.Review,
        area_id: domain.AreaID,
    ) -> domain.Review: ...

    async def read_review(
        self,
        actor: domain.UserID,
        review_id: domain.ReviewID,
    ) -> domain.Review | None: ...

    async def update_review(
        self,
        actor: domain.UserID,
        review_id: domain.ReviewID,
        update: UpdateReview,
    ) -> domain.Review: ...

    async def delete_review(
        self,
        actor: domain.UserID,
        review_id: domain.ReviewID,
    ) -> domain.Review: ...

    async def filter_review(
        self,
        actor: domain.UserID,
        filter: FilterReview,
    ) -> list[domain.Review]: ...


class ReviewRepoImpl(ReviewRepo):
    def __init__(self, cache: Cache):
        self._ks = Keyspace("review")
        self._cache = cache

    async def create_review(
        self,
        actor: domain.UserID,
        review: domain.Review,
        area_id: domain.AreaID,
    ) -> domain.Review:
        try:
            db_review = projection(review, area_id=area_id, user_id=actor)
        except ProjectionError as e:
            raise errors.ValidationError("invalid review") from e
        except Exception as e:
            raise errors.InternalServerError("failed to insert review") from e

        try:
            async with database.Review._meta.db.transaction():
                db_review = (await database.Review.insert(db_review).returning(*database.Review.all_columns()).run())[0]
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

    async def read_review(
        self,
        actor: domain.UserID,
        review_id: domain.ReviewID,
    ) -> domain.Review | None:
        try:
            domain_review = await self._cache.get(self._ks.key(review_id.hex), t=domain.Review)
            if domain_review is not None:
                return domain_review

            async with database.Review._meta.db.transaction():
                db_review = (
                    await database.Review.objects()
                    .where(
                        database.Review.id == review_id,
                        database.Review.deleted_at.is_null(),
                    )
                    .first()
                    .run()
                )
                if db_review is None:
                    return None

                domain_review = projection(db_review)

                await self._cache.set(self._ks.key(review_id.hex), domain_review, expire=self._cache.HOT_FEAT)

            return domain_review
        except ProjectionError as e:
            raise errors.InternalServerError("failed to read review") from e
        except Exception as e:
            raise errors.InternalServerError("failed to read review") from e

    async def update_review(
        self,
        actor: domain.UserID,
        review_id: domain.ReviewID,
        update: UpdateReview,
    ) -> domain.Review:
        try:
            await self._cache.invalidate(self._ks.key(review_id.hex))

            values: dict[Column | str, Any] = {}
            if "rating" in update.model_fields_set and update.rating is not None:
                values[database.Review.rating] = update.rating
            if "comment" in update.model_fields_set:  # nullable field, no check for None
                values[database.Review.comment] = update.comment

            async with database.Review._meta.db.transaction():
                db_review = (
                    await database.Review.update(values)
                    .where(
                        database.Review.id == review_id,
                        database.Review.deleted_at.is_null(),
                        database.Review.user == actor,
                    )
                    .returning(*database.Review.all_columns())
                    .run()
                )[0]

                domain_review = projection(db_review, cast_to=domain.Review)

                await self._cache.set(self._ks.key(domain_review.id.hex), domain_review, expire=self._cache.HOT_FEAT)

            return domain_review
        except DataError as e:
            raise errors.ConflictError("invalid data object") from e
        except IndexError as e:
            raise errors.NotFoundError("no such review") from e
        except ProjectionError as e:
            raise errors.ValidationError("invalid review") from e
        except Exception as e:
            raise errors.InternalServerError("failed to update review") from e

    async def delete_review(
        self,
        actor: domain.UserID,
        review_id: domain.ReviewID,
    ) -> domain.Review:
        try:
            await self._cache.invalidate(self._ks.key(review_id.hex))

            async with database.Review._meta.db.transaction():
                db_review = (
                    await database.Review.update({database.Review.deleted_at: datetime.now(UTC)})
                    .where(
                        database.Review.id == review_id,
                        database.Review.deleted_at.is_null(),
                        database.Review.user == actor,
                    )
                    .returning(*database.Review.all_columns())
                    .run()
                )[0]

                domain_review = projection(db_review, cast_to=domain.Review)

            return domain_review
        except IndexError as e:
            raise errors.NotFoundError("no such review found") from e
        except DataError as e:
            raise errors.ConflictError("invalid data object") from e
        except ProjectionError as e:
            raise errors.ValidationError("invalid review") from e
        except Exception as e:
            raise errors.InternalServerError("failed to delete review") from e

    async def filter_review(
        self,
        actor: domain.UserID,
        filter: FilterReview,
    ) -> list[domain.Review]:
        try:
            query = database.Review.objects().where(database.Review.deleted_at.is_null())

            if filter.area_id is not None:
                query = query.where(database.Review.area._.id == filter.area_id)

            db_reviews = await query.run()
            return [projection(db_review) for db_review in db_reviews]
        except ProjectionError as e:
            raise errors.InternalServerError("failed to read reviews") from e
        except Exception as e:
            raise errors.InternalServerError("failed to read reviews") from e
