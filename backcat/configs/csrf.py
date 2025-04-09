from typing import Literal, Self

from pydantic import BaseModel, Field, ValidationError, model_validator


class CSRF(BaseModel):
    enabled: bool = Field(
        default=True,
        description="enable or disable CSRF protection",
    )
    secret: str = Field(default="", description="secret key for CSRF protection")
    cookie_name: str = Field(default="csrftoken")
    cookie_path: str = Field(default="/")
    cookie_secure: bool = Field(default=False)
    cookie_httponly: bool = Field(default=False)
    cookie_samesite: Literal["lax", "strict", "none"] = Field(default="lax")
    cookie_domain: str | None = Field(default=None)

    @model_validator(mode="after")
    def _(self) -> Self:
        if self.enabled and len(self.secret) < 16:
            raise ValidationError("CSRF secret must be at least 16 characters long when CSRF protection is enabled")

        return self
