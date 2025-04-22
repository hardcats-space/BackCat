from pydantic import BaseModel, Field, RedisDsn


class Redis(BaseModel):
    dsn: RedisDsn = Field(description="Redis DSN")
