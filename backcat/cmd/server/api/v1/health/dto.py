from pydantic import BaseModel


class HealthDTO(BaseModel):
    status: str
    version: str
