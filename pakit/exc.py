""" Houses all exceptions. """


class PakitError(Exception):
    """ All exceptions descend from this. """
    pass


class PakitCmdError(PakitError):
    """ The Command's return code was not 0. """
    pass


class PakitCmdTimeout(PakitError):
    """ The Command timed out. """
    pass


class PakitLinkError(PakitError):
    """ A linking error occurred. """
    pass


class PakitFetchError(PakitError):
    """ A problem occurred retrieving source. """
    pass
