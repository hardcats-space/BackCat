from litestar.dto import DTOConfig
from litestar.plugins.pydantic import PydanticDTO
from pydantic import BaseModel

from backcat import domain


class CreatePOIRequest(PydanticDTO[domain.POI]):
    config = DTOConfig(exclude={"id", "created_at", "updated_at", "deleted_at"}, rename_strategy="camel")


class CreatePOIResponse(PydanticDTO[domain.POI]):
    config = DTOConfig(rename_strategy="camel")


class UpdatePOIRequest(PydanticDTO[domain.POI]):
    config = DTOConfig(exclude={"id", "created_at", "updated_at", "deleted_at"}, partial=True, rename_strategy="camel")


class UpdatePOIResponse(PydanticDTO[domain.POI]):
    config = DTOConfig(rename_strategy="camel")


class ReadPOIResponse(PydanticDTO[domain.POI]):
    config = DTOConfig(rename_strategy="camel")


class _ReadManyPOIs(BaseModel):
    data: list[domain.POI]


class ReadManyPOIResponse(PydanticDTO[_ReadManyPOIs]):
    config = DTOConfig(rename_strategy="camel", max_nested_depth=3)
