class EmptyResponseException(Exception):
    pass


class UnexpectedResponseError(Exception):
    pass


class MaxRetriesHitException(Exception):
    pass
