""" Houses all exceptions. """


class PakitError(Exception):
    """ All exceptions descend from this. """
    pass


class PakitCmdError(PakitError):
    """ Something went wrong with a Command. """
    pass


class PakitLinkError(PakitError):
    """ A problem happened while linking. """
    pass


class PakitFetchError(PakitError):
    """ A problem occurred retrieving source. """
    pass
