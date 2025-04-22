from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Generic, Self, TypeVar
from uuid import uuid4

from pydantic import UUID4, BaseModel, Field, ValidationError, model_validator

T = TypeVar("T", bound=UUID4)


class DomainBaseModel(BaseModel, Generic[T], extra="ignore"):
    id: T = Field()

    created_at: datetime = Field()
    updated_at: datetime = Field()
    deleted_at: datetime | None = Field()

    @classmethod
    def new_defaults(cls) -> DomainBaseModel[T]:
        return DomainBaseModel[T](
            id=uuid4(),  # type: ignore
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            deleted_at=None,
        )

    @classmethod
    def new_defaults_kwargs(cls) -> dict[str, Any]:
        return cls.new_defaults().model_dump()

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
