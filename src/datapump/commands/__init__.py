from datapump.util.models import StrictBaseModel


class BaseCommand(StrictBaseModel):
    command: str
