

class Reconciler(object):
    """ Produces estimate of lastindex on the volume.
    """
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
        """
        """
        raise NotImplemented()


