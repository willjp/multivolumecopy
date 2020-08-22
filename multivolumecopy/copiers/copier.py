import abc
from multivolumecopy import copyoptions


class Copier(object):
    """ Performs copy operation, manages request for drive swap.
    """
    __metaclass__ = abc.ABCMeta

    def __init__(self, source, options=None):
        """
        Args:
            source (CopySource):
                CopySource object, determines files to be copied.

            output (str): ``(ex: '/mnt/backup' )``
                The directory you'd like to backup to.

            options (CopyOptions, None):
                Options to use while performing copy
        """
        self._source = source
        self._options = options or copyoptions.CopyOptions()
        super(Copier, self).__init__()

    @property
    def options(self):
        """ The provided CopyOptions (output, padding, ...).
        """
        return self._options

    @property
    def source(self):
        """ The Resolver used to find files.
        """
        return self._source


    def start(self):
        """ Copies files, prompting for new device when device is full.
        """
        raise NotImplementedError()

    def write_indexfile(self, index):
        """ Dumps last completed index to file.
        """
        with open(self.options.indexfile, 'w') as fd:
            fd.write(str(index))

