import litestar
from litestar.dto import DTOData

from backcat import domain
from backcat.cmd.server.api.v1.area import dto


class Controller(litestar.Controller):
    path = "/area"

    @litestar.post("", dto=dto.CreateAreaRequest, return_dto=dto.CreateAreaResponse)
    async def create(self, data: DTOData[domain.Area]) -> domain.Area:
        return domain.area.AreaFactory.build()

    @litestar.get("/{id:uuid}", return_dto=dto.ReadAreaResponse)
    async def read_one(self, id: domain.AreaID) -> domain.Area:
        return domain.area.AreaFactory.build()

    @litestar.get("", return_dto=dto.ReadManyAreasResponse)
    async def read_many(self, camping_id: domain.CampingID) -> dto._ReadManyAreas:
        return dto._ReadManyAreas(data=[domain.area.AreaFactory.build() for i in range(3)])

    @litestar.patch("/{id:uuid}", dto=dto.UpdateAreaRequest, return_dto=dto.UpdateAreaResponse)
    async def update(self, id: domain.AreaID, data: DTOData[domain.Area]) -> domain.Area:
        return domain.area.AreaFactory.build()

    @litestar.delete("/{id:uuid}")
    async def delete(self, id: domain.AreaID) -> None:
        return None
