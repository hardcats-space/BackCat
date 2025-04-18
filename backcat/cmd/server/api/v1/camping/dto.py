from typing import Literal

from litestar.dto import DTOConfig
from litestar.plugins.pydantic import PydanticDTO
from pydantic import BaseModel

from backcat import domain


class CreateCampingRequest(PydanticDTO[domain.Camping]):
    config = DTOConfig(exclude={"id", "created_at", "updated_at", "deleted_at", "thumbnails"})


class CreateCampingResponse(PydanticDTO[domain.Camping]):
    config = DTOConfig()


class UpdateCampingRequest(PydanticDTO[domain.Camping]):
    config = DTOConfig(exclude={"id", "created_at", "updated_at", "deleted_at", "thumbnails"}, partial=True)


class UpdateCampingResponse(PydanticDTO[domain.Camping]):
    config = DTOConfig()


class ReadCampingResponse(PydanticDTO[domain.Camping]):
    config = DTOConfig()


type Group = Literal["all", "my", "booked"]


class _ReadManyCampingsItem(domain.Camping):
    group: Group


class _ReadManyCampings(BaseModel):
    data: list[_ReadManyCampingsItem]


class ReadManyCampingResponse(PydanticDTO[_ReadManyCampings]):
    config = DTOConfig()
