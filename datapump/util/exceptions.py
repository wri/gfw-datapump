class EmptyResponseException(Exception):
    pass


class UnexpectedResponseError(Exception):
    pass


class DataApiResponseError(Exception):
    pass


class MaxRetriesHitException(Exception):
    pass


class FailedDatasetUploadException(Exception):
    pass


class StatusMismatchException(Exception):
    pass
