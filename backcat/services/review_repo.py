from typing import Protocol, TypedDict, Unpack

from backcat import domain
from backcat.services.cache import Cache, Keyspace


class UpdateReview(TypedDict):
    rating: int
    comment: str | None


class ReviewRepo(Protocol):
    async def create_review(self, review: domain.Review, area_id: domain.AreaID, user_id: domain.UserID) -> domain.Review: ...
    async def read_review(self, review_id: domain.ReviewID) -> domain.Review | None: ...
    async def read_reviews(self, area_id: domain.AreaID | None, user_id: domain.UserID | None) -> list[domain.Review]: ...
    async def update_review(self, review_id: domain.ReviewID, **update: Unpack[UpdateReview]) -> domain.Review: ...
    async def delete_review(self, review_id: domain.ReviewID) -> domain.Review: ...


class ReviewRepoImpl:
    def __init__(self, cache: Cache):
        self._ks = Keyspace("review")
        self._cache = cache

    async def create_review(self, review: domain.Review, area_id: domain.AreaID, user_id: domain.UserID) -> domain.Review:
        pass

    async def read_review(self, review_id: domain.ReviewID) -> domain.Review | None:
        pass

    async def read_reviews(self, area_id: domain.AreaID | None, user_id: domain.UserID | None) -> list[domain.Review]:
        pass

    async def update_review(self, review_id: domain.ReviewID, **update: Unpack[UpdateReview]) -> domain.Review:
        pass

    async def delete_review(self, review_id: domain.ReviewID) -> domain.Review:
        pass
