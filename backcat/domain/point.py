from typing import Any

from pydantic import BaseModel, ValidationError, model_validator


class Point(BaseModel):
    lat: float
    lon: float

    @model_validator(mode="before")
    @classmethod
    def build_from_array(cls, data: Any) -> Any:
        if isinstance(data, list):
            if len(data) != 2:
                raise ValidationError("invalid point")

            return {"lat": data[0], "lon": data[1]}

        return data
