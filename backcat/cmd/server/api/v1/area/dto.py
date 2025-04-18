from litestar.dto import DTOConfig
from litestar.plugins.pydantic import PydanticDTO
from pydantic import BaseModel

from backcat import domain


class CreateAreaRequest(PydanticDTO[domain.Area]):
    config = DTOConfig(exclude={"id", "created_at", "updated_at", "deleted_at"})


class CreateAreaResponse(PydanticDTO[domain.Area]):
    config = DTOConfig()


class UpdateAreaRequest(PydanticDTO[domain.Area]):
    config = DTOConfig(exclude={"id", "created_at", "updated_at", "deleted_at"}, partial=True)


class UpdateAreaResponse(PydanticDTO[domain.Area]):
    config = DTOConfig()


class ReadAreaResponse(PydanticDTO[domain.Area]):
    config = DTOConfig()


class _ReadManyAreas(BaseModel):
    data: list[domain.Area]


class ReadManyAreasResponse(PydanticDTO[_ReadManyAreas]):
    config = DTOConfig()
