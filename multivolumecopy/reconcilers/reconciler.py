from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
import logging
import abc
import os


POSIX_DEVICE_BUSY_ERRNO = 16

logger = logging.getLogger(__name__)


class Reconciler(object):
    """ Produces estimate of lastindex on the volume.
    """
    __metaclass__ = abc.ABCMeta

    def __init__(self, resolver, options):
        """ Constructor.

        Args:
            resolver (resolver.Resolver):
                Resolver object, determines files to be copied.

            options (copyoptions.CopyOptions):
                Options to use while performing copy
        """
        self._resolver = resolver
        self._options = options

    @property
    def resolver(self):
        return self._resolver

    @property
    def options(self):
        return self._options

    def reconcile(self, copyfiles, copied_indexes):
        """ Deletes files to make room for the backup.

        Args:
            copyfiles (tuple):
                A tuple of `resolver.CopyFile` s

            copied_indexes (list):
                A list of indexes within `copyfiles` that have already
                been copied to another device.
        """
        for filepath in self.calculate(copyfiles, copied_indexes):
            os.remove(filepath)

        for directory in self._find_empty_directories():
            try:
              os.rmdir(directory)
            except(OSError):
                # directories are sorted, starting at bottom.
                # any directories displayed raising this error
                # had no files, but subdirectories. These subdirectories
                # contain files, and they should.
                pass

    def calculate(self, copyfiles, copied_indexes):
        """ Determines files to be deleted to make room for the backup.

        Args:
            copyfiles (tuple):
                A tuple of `resolver.CopyFile` s

            copied_indexes (list):
                A list of indexes within `copyfiles` that have already
                been copied to another device.

        Returns:
            set: set of absolute filepaths to be deleted.
        """
        raise NotImplementedError()

    def _find_empty_directories(self):
        # find and remove empty directories as well
        directories = []
        for (root, _, filenames) in os.walk(self.options.output):
            if not filenames and root != self.options.output:
                directories.append(root)
        # return directories in a safe order for deletion
        return sorted(directories, reverse=True)


