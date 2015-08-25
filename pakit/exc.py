""" Houses all exceptions. """


class PakitError(Exception):
    """ All exceptions descend from this. """
    pass


class PakitRollback(PakitError):
    """ To be thrown internally to trigger a rollback of all actions. """
    pass


class PakitCmdError(PakitError):
    """ Something went wrong with a Command. """
    pass


class PakitRecipeError(PakitError):
    """ Something went wrong with a Recipe> """
    pass


class PakitFetchError(PakitError):
    """ A problem occurred retrieving source. """
    pass
