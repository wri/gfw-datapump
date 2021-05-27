from pydantic import BaseModel, Extra


class StrictBaseModel(BaseModel):
    class Config:
        extra = Extra.forbid
