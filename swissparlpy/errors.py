class SwissParlError(Exception):
    """
    General SwissParl error class to provide a superclass for all other errors
    """


class NoMoreRecordsError(SwissParlError):
    """
    Error to indicate, that there are no more records in the result.
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
