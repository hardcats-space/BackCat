import litestar
from litestar.dto import DTOData

from backcat import domain
from backcat.cmd.server.api.v1.poi import dto


class Controller(litestar.Controller):
    path = "/poi"

    @litestar.post("", dto=dto.CreatePOIRequest, return_dto=dto.CreatePOIResponse)
    async def create(self, data: DTOData[domain.POI], camping_id: domain.CampingID) -> domain.POI:
        return domain.poi.POIFactory.build()

    @litestar.get("/{id:uuid}", return_dto=dto.ReadPOIResponse)
    async def read_one(self, id: domain.POIID) -> domain.POI:
        return domain.poi.POIFactory.build()

    @litestar.get("", return_dto=dto.ReadManyPOIResponse)
    async def read_many(self, camping_id: domain.CampingID) -> dto._ReadManyPOIs:
        return dto._ReadManyPOIs(data=[domain.poi.POIFactory.build() for i in range(3)])

    @litestar.patch("/{id:uuid}", dto=dto.UpdatePOIRequest, return_dto=dto.UpdatePOIResponse)
    async def update(self, id: domain.POIID, data: DTOData[domain.POI]) -> domain.POI:
        return domain.poi.POIFactory.build()

    @litestar.delete("/{id:uuid}")
    async def delete(self, id: domain.POIID) -> None:
        return None
