from datapump.util.models import StrictBaseModel


class SetLatestCommand(StrictBaseModel):
    command: str

    class SetLatestParameters(StrictBaseModel):
        analysis_version: str

    parameters: SetLatestParameters
