import abc


class Resolver(object):
    """ Determines method of obtaining list of copyfiles.
    """
    __metaclass__ = abc.ABCMeta

    def __init__(self, options):
        """ Constructor.

        Args:
            options (CopyOptions, None):
                Options to use while performing copy
        """
        self.options = options

    def get_copyfiles(self, device_start_index=None, start_index=None):
        """ Resolve files to be copied.

        Args:
            device_start_index (int, optional):
                the first index to be recorded on current backup device.

            start_index (int, optional):
                the index to start copying from.
        """
        raise NotImplementedError()

