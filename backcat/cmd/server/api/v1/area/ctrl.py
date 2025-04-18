import litestar
from litestar.dto import DTOData

from backcat import domain
from backcat.cmd.server.api.v1.area import dto


class Controller(litestar.Controller):
    path = "/area"

    @litestar.post("", dto=dto.CreateAreaRequest, return_dto=dto.CreateAreaResponse)
    async def create(self, data: DTOData[domain.Area]) -> domain.Area:
        raise NotImplementedError

    @litestar.get("/{id:uuid}", return_dto=dto.ReadAreaResponse)
    async def read_one(self, id: domain.AreaID) -> domain.Area:
        raise NotImplementedError

    @litestar.get("", return_dto=dto.ReadManyAreasResponse)
    async def read_many(self, camping_id: domain.CampingID) -> dto._ReadManyAreas:
        raise NotImplementedError

    @litestar.patch("/{id:uuid}", dto=dto.UpdateAreaRequest, return_dto=dto.UpdateAreaResponse)
    async def update(self, id: domain.AreaID, data: DTOData[domain.Area]) -> domain.Area:
        raise NotImplementedError

    @litestar.delete("/{id:uuid}")
    async def delete(self, id: domain.AreaID) -> None:
        raise NotImplementedError
