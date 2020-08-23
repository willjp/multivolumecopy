import abc


class Resolver(object):
    """ Determines method of obtaining list of copyfiles.
    """
    __metaclass__ = abc.ABCMeta

    def __init__(self, options):
        self.options = options

    def get_copyfiles(self, device_start_index=None, start_index=None):
        raise NotImplementedError()

