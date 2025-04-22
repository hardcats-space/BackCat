import litestar
from litestar.dto import DTOData

from backcat import domain
from backcat.cmd.server.api.v1.camping import dto


class Controller(litestar.Controller):
    path = "/camping"

    @litestar.post("", dto=dto.CreateCampingRequest, return_dto=dto.CreateCampingResponse)
    async def create(self, data: DTOData[domain.Camping]) -> domain.Camping:
        return domain.camping.CampingFactory.build()

    @litestar.get("/{id:uuid}", return_dto=dto.ReadCampingResponse)
    async def read_one(self, id: domain.CampingID) -> domain.Camping:
        return domain.camping.CampingFactory.build()

    @litestar.get("", return_dto=dto.ReadManyCampingResponse)
    async def read_many(self, group: dto.Group) -> dto._ReadManyCampings:
        return dto._ReadManyCampings(data=[
            dto._ReadManyCampingsItem(**domain.camping.CampingFactory.build().model_dump(), group=group)
            for i in range(3)
        ])

    @litestar.patch("/{id:uuid}", dto=dto.UpdateCampingRequest, return_dto=dto.UpdateCampingResponse)
    async def update(self, id: domain.CampingID, data: DTOData[domain.Camping]) -> domain.Camping:
        return domain.camping.CampingFactory.build()

    @litestar.delete("/{id:uuid}")
    async def delete(self, id: domain.CampingID) -> None:
        return None
