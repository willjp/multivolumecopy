import abc
import json
import os
from multivolumecopy import copyoptions


class Copier(object):
    """ Performs copy operation, manages request for drive swap.
    """
    __metaclass__ = abc.ABCMeta

    def __init__(self, resolver, options=None):
        """
        Args:
            source (resolver.Resolver):
                Resolver, determines files to be copied.

            output (str): ``(ex: '/mnt/backup' )``
                The directory you'd like to backup to.

            options (CopyOptions, None):
                Options to use while performing copy
        """
        self._resolver = resolver
        self._options = options or copyoptions.CopyOptions()
        super(Copier, self).__init__()

    @property
    def options(self):
        """ The provided CopyOptions (output, padding, ...).
        """
        return self._options

    @property
    def resolver(self):
        """ The Resolver used to find files.
        """
        return self._resolver

    def start(self):
        """ Copies files, prompting for new device when device is full.
        """
        raise NotImplementedError()

    def write_jobfile(self, copyfiles):
        """ Writes the jobfile.

        Jobfile contains info about all files to be copied.
        (You can resume progress if you have this file).
        """
        with open(self.options.jobfile, 'w') as fd:
            fd.write(json.dumps(copyfiles, indent=2))

    def remove_jobfile(self):
        """ Removes the jobfile.

        Jobfile contains info about all files to be copied.
        (You can resume progress if you have this file).
        """
        if os.path.isfile(self.options.jobfile):
            os.remove(self.options.jobfile)

    def create_progressfile(self):
        pass

    def create_errorfile(self):
        pass

    def append_progressfile(self):
        pass

    def append_errorfile(self):
        pass
