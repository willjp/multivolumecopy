import abc


class Resolver(object):
    """ Determines method of obtaining list of copyfiles.
    """
    __metaclass__ = abc.ABCMeta

    def get_copyfiles(self):
        raise NotImplementedError()

