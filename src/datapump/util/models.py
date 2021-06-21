from pydantic import BaseModel, Extra, Field

DATE_REGEX = r"^\d{4}(\-(0?[1-9]|1[012])\-(0?[1-9]|[12][0-9]|3[01]))?$"


class StrictBaseModel(BaseModel):
    class Config:
        extra = Extra.forbid


class ContentDateRange(StrictBaseModel):
    min: str = Field(
        ...,
        description="Beginning date covered by data",
        regex=DATE_REGEX,
    )
    max: str = Field(
        ...,
        description="End date covered by data",
        regex=DATE_REGEX,
    )
