from typing import Protocol, TypedDict, Unpack

from backcat import domain
from backcat.domain import Point
from backcat.services.cache import Cache, Keyspace


class UpdateCamping(TypedDict):
    polygon: list[Point]
    title: str
    description: str | None
    thumbnails: list[str]


class CampingRepo(Protocol):
    async def create_camping(self, camping: domain.Camping, user_id: domain.UserID) -> domain.Camping: ...
    async def read_camping(self, camping_id: domain.CampingID) -> domain.Camping | None: ...
    async def read_campings(self, user_id: domain.UserID | None) -> list[domain.Camping]: ...
    async def update_camping(self, camping_id: domain.CampingID, **update: Unpack[UpdateCamping]) -> domain.Camping: ...
    async def delete_camping(self, camping_id: domain.CampingID) -> domain.Camping: ...


class CampingRepoImpl:
    def __init__(self, cache: Cache):
        self._ks = Keyspace("camping")
        self._cache = cache

    async def create_camping(self, camping: domain.Camping, user_id: domain.UserID) -> domain.Camping:
        pass

    async def read_camping(self, camping_id: domain.CampingID) -> domain.Camping | None:
        pass

    async def read_campings(self, user_id: domain.UserID | None) -> list[domain.Camping]:
        pass

    async def update_camping(self, camping_id: domain.CampingID, **update: Unpack[UpdateCamping]) -> domain.Camping:
        pass

    async def delete_camping(self, camping_id: domain.CampingID) -> domain.Camping:
        pass
