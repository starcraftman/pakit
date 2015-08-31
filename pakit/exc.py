"""
All pakit exceptions are subclasses of PakitError
"""


class PakitError(Exception):
    """
    The base pakit exception, indicates general failure.
    """
    pass


class PakitCmdError(PakitError):
    """
    The Command finished and the return code indicated failure.
    """
    pass


class PakitCmdTimeout(PakitError):
    """
    The Command timed out after writing no stdout for max_time.
    """
    pass


class PakitLinkError(PakitError):
    """
    An error occurred during linking.
    """
    pass


class PakitFetchError(PakitError):
    """
    The source could not be retrieved.
    """
    pass
