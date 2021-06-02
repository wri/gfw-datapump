from datapump.util.models import StrictBaseModel


class SetLatestParameters(StrictBaseModel):
    analysis_version: str


class SetLatestCommand(StrictBaseModel):
    command: str
    parameters: SetLatestParameters
