from datapump.commands import BaseCommand


class SetLatestParameters(BaseCommand):
    analysis_version: str


class SetLatestCommand(BaseCommand):
    command: str
    parameters: SetLatestParameters
