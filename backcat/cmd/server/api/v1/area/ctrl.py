from typing import Annotated, Any

import litestar
from dishka.integrations.litestar import FromDishka, inject
from litestar.dto import DTOData
from litestar.exceptions import NotFoundException
from litestar.params import Parameter

from backcat import domain, services
from backcat.cmd.server.api.v1.area import dto


class Controller(litestar.Controller):
    path = "/area"
    tags = ["area"]

    @litestar.post("", dto=dto.CreateAreaRequest, return_dto=dto.CreateAreaResponse)
    @inject
    async def create(
        self,
        camping_id: Annotated[domain.CampingID, Parameter(query="campingId")],
        data: DTOData[domain.Area],
        request: litestar.Request[domain.User, Any, Any],
        area_repo: FromDishka[services.AreaRepo],
    ) -> domain.Area:
        return await area_repo.create_area(
            request.user.id,
            data.create_instance(**domain.Area.new_defaults_kwargs()),
            camping_id,
        )

    @litestar.get("/{id:uuid}", return_dto=dto.ReadAreaResponse)
    @inject
    async def read_one(
        self,
        id: domain.AreaID,
        request: litestar.Request[domain.User, Any, Any],
        area_repo: FromDishka[services.AreaRepo],
    ) -> domain.Area:
        area = await area_repo.read_area(request.user.id, id)
        if area is None:
            raise NotFoundException(detail="area not found")
        return area

    @litestar.get("", return_dto=dto.ReadManyAreasResponse)
    @inject
    async def read_many(
        self,
        camping_id: domain.CampingID,
        request: litestar.Request[domain.User, Any, Any],
        area_repo: FromDishka[services.AreaRepo],
    ) -> dto._ReadManyAreas:
        return dto._ReadManyAreas(
            data=await area_repo.filter_area(
                request.user.id,
                services.area_repo.FilterArea(camping_id=camping_id),
            )
        )

    @litestar.patch("/{id:uuid}", dto=dto.UpdateAreaRequest, return_dto=dto.UpdateAreaResponse)
    @inject
    async def update(
        self,
        id: domain.AreaID,
        data: DTOData[domain.Area],
        request: litestar.Request[domain.User, Any, Any],
        area_repo: FromDishka[services.AreaRepo],
    ) -> domain.Area:
        return await area_repo.update_area(
            request.user.id,
            id,
            services.area_repo.UpdateArea.model_validate(data.as_builtins()),
        )

    @litestar.delete("/{id:uuid}")
    @inject
    async def delete(
        self,
        id: domain.AreaID,
        request: litestar.Request[domain.User, Any, Any],
        area_repo: FromDishka[services.AreaRepo],
    ) -> None:
        await area_repo.delete_area(request.user.id, id)
