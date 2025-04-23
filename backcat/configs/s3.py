from pydantic import BaseModel, Field
from pydantic_extra_types.domain import DomainStr


class S3(BaseModel):
    endpoint: DomainStr = Field(description="S3 endpoint")
    bucket: str = Field(description="S3 bucket name")
    region: str | None = Field(None, description="S3 region")
    access_key: str | None = Field(None, description="S3 access token")
    secret_key: str | None = Field(None, description="S3 secret token")
    public_endpoint: DomainStr | None = Field(None, description="S3 public root")
