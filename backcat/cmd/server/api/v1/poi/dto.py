from litestar.dto import DTOConfig
from litestar.plugins.pydantic import PydanticDTO
from pydantic import BaseModel

from backcat import domain


class CreatePOIRequest(PydanticDTO[domain.POI]):
    config = DTOConfig(exclude={"id", "created_at", "updated_at", "deleted_at"})


class CreatePOIResponse(PydanticDTO[domain.POI]):
    config = DTOConfig()


class UpdatePOIRequest(PydanticDTO[domain.POI]):
    config = DTOConfig(exclude={"id", "created_at", "updated_at", "deleted_at"}, partial=True)


class UpdatePOIResponse(PydanticDTO[domain.POI]):
    config = DTOConfig()


class ReadPOIResponse(PydanticDTO[domain.POI]):
    config = DTOConfig()


class _ReadManyPOIs(BaseModel):
    data: list[domain.POI]


class ReadManyPOIResponse(PydanticDTO[_ReadManyPOIs]):
    config = DTOConfig()
