from pydantic import BaseModel, Field, ValidationError, field_validator


class CORS(BaseModel):
    allow_origins: list[str] = Field(
        default=["*"],
        description="a list of origins that should be permitted",
    )
    allow_methods: list[str] = Field(
        default_factory=lambda: ["*"],
        description="a list of HTTP methods that should be allowed.",
    )
    allow_headers: list[str] = Field(
        default_factory=lambda: ["*"],
        description="a list of HTTP request headers that should be supported",
    )
    allow_credentials: bool = Field(
        default=False,
        description="indicate that cookies should be supported",
    )
    expose_headers: list[str] = Field(
        default_factory=lambda: [],
        description="a list of HTTP headers that should be exposed",
    )
    max_age: int = Field(
        default=300,
        description="the maximum age of the CORS headers",
        ge=0,
    )

    @field_validator("allow_methods", mode="before")
    @classmethod
    def _(cls, allow_methods: list[str]) -> list[str]:
        if allow_methods == ["*"]:
            return allow_methods

        for method in allow_methods:
            if method not in ["GET", "POST", "PUT", "DELETE", "OPTIONS"]:
                raise ValidationError(f"Invalid CORS method: {method}")

        return allow_methods
