from datetime import datetime
from typing import Generic, Self, TypeVar

from pydantic import UUID4, BaseModel, Extra, Field, ValidationError, model_validator

T = TypeVar("T", bound=UUID4)


class DomainBaseModel(BaseModel, Generic[T], extra=Extra.ignore):
    id: T = Field()

    created_at: datetime = Field()
    updated_at: datetime = Field()
    deleted_at: datetime = Field()

    @model_validator(mode="after")
    def _(self) -> Self:
        if self.created_at.tzinfo is None:
            raise ValidationError("created_at must contain timezone")

        if self.updated_at.tzinfo is None:
            raise ValidationError("updated_at must contain timezone")

        if self.deleted_at is not None and self.deleted_at.tzinfo is None:
            raise ValidationError("deleted_at must contain timezone")

        if self.updated_at < self.created_at:
            raise ValidationError("updated_at cannot be before created_at")

        if self.deleted_at is not None and self.deleted_at < self.created_at:
            raise ValidationError("deleted_at cannot be before created_at")

        return self
