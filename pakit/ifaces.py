"""
Shared holder of interfaces for the project.
"""
from __future__ import absolute_import

from abc import ABCMeta, abstractmethod, abstractproperty

from paksys.cmd import Command


class Fetchable(object):
    """
    Establishes an abstract interface for fetching source code.

    Subclasses are destined for Recipe.repos to be used to retrieve source
    from the wild.

    Attributes:
        target: The folder the source code should end up in.
        uri: The location of the source code.
    """
    __metaclass__ = ABCMeta

    def __init__(self, uri, target):
        self.target = target
        self.uri = uri

    @abstractmethod
    def __enter__(self):
        """
        Guarantees that source is available at target
        """
        raise NotImplementedError

    @abstractmethod
    def __exit__(self, exc_type, exc_value, exc_tb):
        """
        Handles errors as needed
        """
        raise NotImplementedError

    @abstractproperty
    def ready(self):
        """
        True iff the source code is available at target
        """
        raise NotImplementedError

    @abstractproperty
    def src_hash(self):
        """
        A hash that identifies the source snapshot
        """
        raise NotImplementedError

    def clean(self):
        """
        Purges the source tree from the system
        """
        Command('rm -rf ' + self.target)

    @abstractmethod
    def download(self):
        """
        Retrieves code from the remote, may require additional steps
        """
        raise NotImplementedError
