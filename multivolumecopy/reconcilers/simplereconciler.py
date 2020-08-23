

class SimpleReconciler(reconciler.Reconciler):
    """ Checks space on selected volume, calculates filesize sums and provides last index.

    Notes:
        This is the simplest resolver, but it is flawed. Filesystems may use compression
        on one side, but not the other resulting in dramatic differences in sizes.
    """
    def __init__(self, source, options):
        super(SimpleReconciler, self).__init__(source, options)

    def estimate_lastindex(self):
        capacity = filesystem.avail_bytes_for_backup(self.options.output)
        capacity -= self.options.device_padding

        # determine which/how-many srcfiles to copy to this volume
        lastindex = index
        copysize = 0
        while lastindex + 1 < len(copyfiles):
            copysize += copyfiles[lastindex]['bytes']

            if copysize < capacity:
                lastindex += 1
            else:
                break

        if lastindex < 0:
            raise RuntimeError('volume does not have sufficient space to copy files')

        return lastindex
