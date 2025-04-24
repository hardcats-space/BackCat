from typing import Annotated, Any

import litestar
from dishka.integrations.litestar import FromDishka, inject
from litestar.datastructures import UploadFile
from litestar.dto import DTOData
from litestar.enums import RequestEncodingType
from litestar.exceptions import NotFoundException
from litestar.params import Body

from backcat import domain, services
from backcat.cmd.server.api.v1.camping import dto


class Controller(litestar.Controller):
    path = "/camping"
    tags = ["camping"]

    @litestar.post("", dto=dto.CreateCampingRequest, return_dto=dto.CreateCampingResponse)
    @inject
    async def create(
        self,
        data: DTOData[domain.Camping],
        request: litestar.Request[domain.User, Any, Any],
        camping_repo: FromDishka[services.CampingRepo],
    ) -> domain.Camping:
        return await camping_repo.create_camping(
            request.user.id,
            data.create_instance(**domain.Camping.new_defaults_kwargs()),
        )

    @litestar.get("/{id:uuid}", return_dto=dto.ReadCampingResponse)
    @inject
    async def read_one(
        self,
        id: domain.CampingID,
        request: litestar.Request[domain.User, Any, Any],
        camping_repo: FromDishka[services.CampingRepo],
    ) -> domain.Camping:
        camping = await camping_repo.read_camping(request.user.id, id)
        if camping is None:
            raise NotFoundException(detail="camping not found")
        return camping

    @litestar.get("", return_dto=dto.ReadManyCampingResponse)
    @inject
    async def read_many(
        self,
        group: dto.Group,
        request: litestar.Request[domain.User, Any, Any],
        camping_repo: FromDishka[services.CampingRepo],
    ) -> dto._ReadManyCampings:
        campings = []

        if group == "all":
            campings = await camping_repo.filter_camping(
                request.user.id,
                services.camping_repo.FilterCamping(),
            )

        if group == "my":
            campings = await camping_repo.filter_camping(
                request.user.id,
                services.camping_repo.FilterCamping(user_id=request.user.id),
            )

        if group == "booked":
            campings = await camping_repo.filter_camping(
                request.user.id,
                services.camping_repo.FilterCamping(booked=True, user_id=request.user.id),
            )

        return dto._ReadManyCampings(
            data=campings
        )

    @litestar.patch("/{id:uuid}", dto=dto.UpdateCampingRequest, return_dto=dto.UpdateCampingResponse)
    @inject
    async def update(
        self,
        id: domain.CampingID,
        data: DTOData[domain.Camping],
        request: litestar.Request[domain.User, Any, Any],
        camping_repo: FromDishka[services.CampingRepo],
    ) -> domain.Camping:
        return await camping_repo.update_camping(
            request.user.id,
            id,
            services.camping_repo.UpdateCamping.model_validate(data.as_builtins()),
        )

    @litestar.delete("/{id:uuid}")
    @inject
    async def delete(
        self,
        id: domain.CampingID,
        request: litestar.Request[domain.User, Any, Any],
        camping_repo: FromDishka[services.CampingRepo],
    ) -> None:
        await camping_repo.delete_camping(request.user.id, id)

    @litestar.post("/{id:uuid}/thumbnail", return_dto=dto.UpdateCampingResponse)
    @inject
    async def add_thumbnail(
        self,
        id: domain.CampingID,
        request: litestar.Request[domain.User, Any, Any],
        data: Annotated[UploadFile, Body(media_type=RequestEncodingType.MULTI_PART)],
        camping_repo: FromDishka[services.CampingRepo],
    ) -> domain.Camping:
        content = await data.read()
        return await camping_repo.upload_thumbnail(request.user.id, id, content)  # type: ignore

    @litestar.delete("/{id:uuid}/thumbnail/{index:int}", return_dto=dto.UpdateCampingResponse, status_code=200)
    @inject
    async def remove_thumbnail(
        self,
        id: domain.CampingID,
        index: int,
        request: litestar.Request[domain.User, Any, Any],
        camping_repo: FromDishka[services.CampingRepo],
    ) -> domain.Camping:
        return await camping_repo.remove_thumbnail(request.user.id, id, index)
