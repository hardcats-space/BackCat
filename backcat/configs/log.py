from typing import Literal

from pydantic import BaseModel, Field


class Log(BaseModel):
    level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(default="DEBUG")
