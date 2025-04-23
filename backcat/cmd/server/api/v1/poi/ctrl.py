from typing import Annotated, Any

import litestar
from dishka.integrations.litestar import FromDishka, inject
from litestar.dto import DTOData
from litestar.exceptions import NotFoundException
from litestar.params import Parameter

from backcat import domain, services
from backcat.cmd.server.api.v1.poi import dto


class Controller(litestar.Controller):
    path = "/poi"
    tags = ["poi"]

    @litestar.post("", dto=dto.CreatePOIRequest, return_dto=dto.CreatePOIResponse)
    @inject
    async def create(
        self,
        camping_id: Annotated[domain.CampingID, Parameter(query="campingId")],
        data: DTOData[domain.POI],
        request: litestar.Request[domain.User, Any, Any],
        poi_repo: FromDishka[services.POIRepo],
    ) -> domain.POI:
        return await poi_repo.create_poi(
            request.user.id,
            data.create_instance(**domain.POI.new_defaults_kwargs()),
            camping_id,
        )

    @litestar.get("/{id:uuid}", return_dto=dto.ReadPOIResponse)
    @inject
    async def read_one(
        self,
        id: domain.POIID,
        request: litestar.Request[domain.User, Any, Any],
        poi_repo: FromDishka[services.POIRepo],
    ) -> domain.POI:
        poi = await poi_repo.read_poi(request.user.id, id)
        if poi is None:
            raise NotFoundException(detail="poi not found")
        return poi

    @litestar.get("", return_dto=dto.ReadManyPOIResponse)
    @inject
    async def read_many(
        self,
        camping_id: Annotated[domain.CampingID, Parameter(query="campingId")],
        request: litestar.Request[domain.User, Any, Any],
        poi_repo: FromDishka[services.POIRepo],
    ) -> dto._ReadManyPOIs:
        return dto._ReadManyPOIs(
            data=await poi_repo.filter_poi(
                request.user.id,
                services.poi_repo.FilterPOI(camping_id=camping_id),
            )
        )

    @litestar.patch("/{id:uuid}", dto=dto.UpdatePOIRequest, return_dto=dto.UpdatePOIResponse)
    @inject
    async def update(
        self,
        id: domain.POIID,
        data: DTOData[domain.POI],
        request: litestar.Request[domain.User, Any, Any],
        poi_repo: FromDishka[services.POIRepo],
    ) -> domain.POI:
        return await poi_repo.update_poi(
            request.user.id,
            id,
            services.poi_repo.UpdatePOI.model_validate(data.as_builtins()),
        )

    @litestar.delete("/{id:uuid}")
    @inject
    async def delete(
        self,
        id: domain.POIID,
        request: litestar.Request[domain.User, Any, Any],
        poi_repo: FromDishka[services.POIRepo],
    ) -> None:
        await poi_repo.delete_poi(request.user.id, id)
