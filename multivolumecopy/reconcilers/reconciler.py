

class Reconciler(object):
    """ Produces estimate of lastindex on the volume.
    """
    def __init__(self, copyfiles, options):
        self._copyfiles = copyfiles
        self._options = options

    @property
    def copyfiles(self):
        return self._copyfiles

    @property
    def options(self):
        return self._options

    def reconcile(self, copyfiles, copied_indexes):
        """
        """
        raise NotImplemented()


