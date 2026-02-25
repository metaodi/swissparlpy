class SwissParlError(Exception):
    """
    General SwissParl error class to provide a superclass for all other errors
    """


class NoMoreRecordsError(SwissParlError):
    """
    Error to indicate, that there are no more records in the result.
    """


class TableNotFoundError(SwissParlError):
    """
    Error to indicate, that a requested table was not found in the backend.
    """


class SwissParlTimeoutError(SwissParlError):
    """
    Error to indicate, that the server returned a timeout error.
    """


class SwissParlHttpRequestError(SwissParlError):
    """
    Error to indicate, that there was an HTTP request error.
    """


class SwissParlWarning(Warning):
    """
    General SwissParl warning class to provide a superclass for all warnings
    """


class ResultVeryLargeWarning(SwissParlWarning):
    """
    A warning to indicate, that a result is very large.
    The query should be split up to reduce memory usage.
    """


class OutdatedDataWarning(SwissParlWarning):
    """
    A warning to indicate, that the provided data is outdated and might not be accurate.
    """


class PaginationWarning(SwissParlWarning):
    """
    A warning to indicate that there was a problem with pagination,
    such as loading more records than the total count.
    """
