from typing import Protocol, TypedDict, Unpack

from backcat import domain
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

    async def create_poi(self, poi: domain.POI, camping_id: domain.CampingID) -> domain.POI: ...

    async def read_poi(self, poi_id: domain.POIID) -> domain.POI | None: ...

    async def read_pois(self, camping_id: domain.CampingID) -> list[domain.POI]: ...

    async def update_poi(self, poi_id: domain.POIID, **update: Unpack[UpdatePOI]) -> domain.POI: ...

    async def delete_poi(self, poi_id: domain.POIID) -> domain.POI: ...
