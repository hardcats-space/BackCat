from litestar.dto import DTOConfig
from litestar.plugins.pydantic import PydanticDTO
from pydantic import BaseModel

from backcat import domain


class CreateReviewRequest(PydanticDTO[domain.Review]):
    config = DTOConfig(exclude={"id", "created_at", "updated_at", "deleted_at"}, rename_strategy="camel")


class CreateReviewResponse(PydanticDTO[domain.Review]):
    config = DTOConfig(rename_strategy="camel")


class UpdateReviewRequest(PydanticDTO[domain.Review]):
    config = DTOConfig(exclude={"id", "created_at", "updated_at", "deleted_at"}, partial=True, rename_strategy="camel")


class UpdateReviewResponse(PydanticDTO[domain.Review]):
    config = DTOConfig(rename_strategy="camel")


class ReadReviewResponse(PydanticDTO[domain.Review]):
    config = DTOConfig(rename_strategy="camel")


class _ReadManyReviews(BaseModel):
    data: list[domain.Review]


class ReadManyReviewResponse(PydanticDTO[_ReadManyReviews]):
    config = DTOConfig(rename_strategy="camel")
