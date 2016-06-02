"""
All version control logic.
"""
from __future__ import absolute_import

import inspect
import os
import sys
from abc import abstractmethod, abstractproperty

from pakit.exc import PakitError
from pakit.ifaces import Fetchable
from paksys.cmd import Command


def vcs_factory(uri, **kwargs):
    """
    Given a uri, match it with the right VersionRepo subclass.

    Args:
        uri: The version control URI.

    Returns:
        The instantiated VersionRepo subclass. Any kwargs, are
        passed along to the constructor of the subclass.

    Raises:
        PakitError: The URI is not supported.
    """
    subclasses = []
    for _, obj in inspect.getmembers(sys.modules[__name__]):
        if inspect.isclass(obj) and issubclass(obj, VersionRepo):
            subclasses.append(obj)
    subclasses.remove(VersionRepo)

    for cls in subclasses:
        if cls.valid_uri(uri):
            return cls(uri, **kwargs)

    raise PakitError('Unssupported URI: ' + uri)


class VersionRepo(Fetchable):
    """
    Base class for all version control support.

    When a 'tag' is set, check out a specific revision of the repository.
    When a 'branch' is set, checkout out the latest commit on the branch of
    the repository.
    These two options are mutually exclusive.

    Attributes:
        branch: A branch to checkout during clone.
        src_hash: The hash of the current commit.
        tag: A tag to checkout during clone.
        target: The folder the source code should end up in.
        uri: The location of the source code.
    """
    def __init__(self, uri, **kwargs):
        super(VersionRepo, self).__init__(uri, kwargs.get('target', None))
        tag = kwargs.get('tag', None)
        if tag is not None:
            self.__tag = tag
            self.on_branch = False
        else:
            self.__tag = kwargs.get('branch', None)
            self.on_branch = True

    def __enter__(self):
        """
        Guarantees that the repo is downloaded and on the right commit.
        """
        if not self.ready:
            self.clean()
            self.download()
        else:
            self.checkout()
            if self.on_branch:
                self.update()

    def __exit__(self, exc_type, exc_value, exc_tb):
        """
        Handles errors as needed
        """
        self.reset()

    def __str__(self):
        if self.on_branch:
            tag = 'HEAD' if self.tag is None else self.tag
            tag = 'branch: ' + tag
        else:
            tag = 'tag: ' + self.tag
        return '{name}: {tag}, uri: {uri}'.format(
            name=self.__class__.__name__, uri=self.uri, tag=tag)

    @property
    def branch(self):
        """
        A branch of the repository.
        """
        return self.__tag

    @branch.setter
    def branch(self, new_branch):
        """
        Set the branch to checkout from the repository.
        """
        self.on_branch = True
        self.__tag = new_branch

    @property
    def tag(self):
        """
        A revision or tag of the repository.
        """
        return self.__tag

    @tag.setter
    def tag(self, new_tag):
        """
        Set the tag to checkout from the repository.
        """
        self.on_branch = False
        self.__tag = new_tag

    @abstractproperty
    def ready(self):
        """
        Returns true iff the repository is available and the
        right tag or branch is checked out.
        """
        raise NotImplementedError

    @abstractproperty
    def src_hash(self):
        """
        The hash of the current commit.
        """
        raise NotImplementedError

    @staticmethod
    def valid_uri(uri):
        """
        Validate that the supplied uri is handled by this class.

        Returns:
            True if the URI is valid for this class, else False.
        """
        raise NotImplementedError

    @abstractmethod
    def checkout(self):
        """
        Equivalent to git checkout for the version system.
        """
        raise NotImplementedError

    @abstractmethod
    def download(self):
        """
        Download the repository to the target.
        """
        raise NotImplementedError

    @abstractmethod
    def reset(self):
        """
        Clears away all build files from repo.
        """
        raise NotImplementedError

    @abstractmethod
    def update(self):
        """
        Fetches latest commit when branch is set.
        """
        raise NotImplementedError


class Git(VersionRepo):
    """
    Fetch a git repository from the given URI.

    When a 'tag' is set, check out a specific revision of the repository.
    When a 'branch' is set, checkout out the latest commit on the branch of
    the repository.
    If neither provided, will checkout 'master' branch.
    These two options are mutually exclusive.

    Attributes:
        branch: A branch to checkout during clone.
        src_hash: The hash of the current commit.
        tag: A tag to checkout during clone.
        target: The folder the source code should end up in.
        uri: The location of the source code.
    """
    def __init__(self, uri, **kwargs):
        """
        Constructor for a git repository.
        By default checks out the default branch.
        The *branch* and *tag* kwargs are mutually exclusive.

        Args:
            uri: The URI that hosts the repository.

        Kwargs:
            branch: A branch to checkout and track.
            tag: Any fixed tag like a revision or tagged commit.
            target: Path on system to clone to.
        """
        super(Git, self).__init__(uri, **kwargs)
        if self.on_branch and kwargs.get('tag') is None:
            self.branch = 'master'

    @property
    def ready(self):
        """
        Returns true iff the repository is available and
        the right tag or branch is checked out.
        """
        if not os.path.exists(os.path.join(self.target, '.git')):
            return False

        cmd = Command('git remote show origin', self.target)
        return self.uri in cmd.output()[1]

    @property
    def src_hash(self):
        """
        Return the current hash of the repository.
        """
        with self:
            cmd = Command('git rev-parse HEAD', self.target)
            return cmd.output()[0]

    @staticmethod
    def valid_uri(uri):
        """
        Validate that the supplied uri is handled by this class.

        Returns:
            True if the URI is valid for this class, else False.
        """
        try:
            cmd = Command('git ls-remote ' + uri)
            return cmd.rcode == 0
        except PakitError:
            return False

    def checkout(self):
        """
        Checkout the right tag or branch.
        """
        Command('git checkout ' + self.tag, self.target)

    def download(self):
        """
        Download the repository to the target.
        """
        tag = '' if self.tag is None else '-b ' + self.tag
        Command('git clone --recursive {tag} {uri} {target}'.format(
            tag=tag, uri=self.uri, target=self.target))

    def reset(self):
        """
        Clears away all build files from repo.
        """
        Command('git clean -f', self.target)

    def update(self):
        """
        Fetches latest commit when branch is set.
        """
        Command('git fetch origin +{0}:new{0}'.format(self.branch),
                self.target)
        Command('git merge --ff-only new' + self.branch, self.target)


class Hg(VersionRepo):
    """
    Fetch a mercurial repository from the given URI.

    When a 'tag' is set, check out a specific revision of the repository.
    When a 'branch' is set, checkout out the latest commit on the branch of
    the repository.
    If neither provided, will checkout 'default' branch.
    These two options are mutually exclusive.

    Attributes:
        branch: A branch to checkout during clone.
        src_hash: The hash of the current commit.
        tag: A tag to checkout during clone.
        target: The folder the source code should end up in.
        uri: The location of the source code.
    """
    def __init__(self, uri, **kwargs):
        """
        Constructor for a mercurial repository.
        By default checks out the default branch.
        The *branch* and *tag* kwargs are mutually exclusive.

        Args:
            uri: The URI that hosts the repository.

        Kwargs:
            branch: A branch to checkout and track.
            tag: Any fixed tag like a revision or tagged commit.
            target: Path on system to clone to.
        """
        super(Hg, self).__init__(uri, **kwargs)
        if self.on_branch and kwargs.get('tag') is None:
            self.branch = 'default'

    @property
    def ready(self):
        """
        Returns true iff the repository is available and the
        right tag or branch is checked out.
        """
        if not os.path.exists(os.path.join(self.target, '.hg')):
            return False

        found = False
        with open(os.path.join(self.target, '.hg', 'hgrc')) as fin:
            for line in fin:
                if self.uri in line:
                    found = True
                    break

        return found

    @property
    def src_hash(self):
        """
        Return the current hash of the repository.
        """
        with self:
            cmd = Command('hg identify', self.target)
            return cmd.output()[0].split()[0]

    @staticmethod
    def valid_uri(uri):
        """
        Validate that the supplied uri is handled by this class.

        Returns:
            True if the URI is valid for this class, else False.
        """
        try:
            cmd = Command('hg identify ' + uri)
            return cmd.rcode == 0
        except PakitError:
            return False

    def checkout(self):
        """
        Checkout the right tag or branch.
        """
        Command('hg update ' + self.tag, self.target)

    def download(self):
        """
        Download the repository to the target.
        """
        tag = '' if self.tag is None else '-u ' + self.tag
        Command('hg clone {tag} {uri} {target}'.format(
            tag=tag, uri=self.uri, target=self.target))

    def reset(self):
        """
        Clears away all build files from repo.
        """
        cmd = Command('hg status -un', self.target)
        for path in cmd.output():
            os.remove(os.path.join(self.target, path))

    def update(self):
        """
        Fetches latest commit when branch is set.
        """
        Command('hg pull -b ' + self.branch, self.target)
        Command('hg update', self.target)
