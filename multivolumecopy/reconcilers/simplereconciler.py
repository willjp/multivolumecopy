from multivolumecopy.reconcilers import reconciler
from multivolumecopy import filesystem
import sys
import os
import logging


# WARNING!!! This is super flawed. See TODO.rst


logger = logging.getLogger(__name__)


class SimpleReconciler(reconciler.Reconciler):
    """ Checks space on selected volume, calculates filesize sums and provides last index.

    Notes:
        This is the simplest resolver, but it is flawed. Filesystems may use compression
        on one side, but not the other resulting in dramatic differences in sizes.
    """
    def __init__(self, source, options):
        super(SimpleReconciler, self).__init__(source, options)

    def estimate_lastindex(self, index, copyfiles):
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

    def reconcile(self, copyfiles, copied_indexes):
        # NOTE: this is broken/innaccurate. just leave it, replacing.
        index = copied_index[-1]
        lastindex = self.estimate_lastindex(index, copyfiles)

        # get a list of all dstfiles that will be copied to this volume
        dstfiles = set()
        i = index
        while i <= lastindex:
            copyfile = copyfiles[i]
            dstfiles.add(copyfile['dst'])
            i += 1

        # obtain list of files to delete (files not included in list of srcfiles)
        deletefiles = set()
        for (root, dirnames, filenames) in os.walk(self.options.output):
            for filename in filenames:
                filepath = os.path.abspath('{}/{}'.format(root, filename))

                if filepath not in dstfiles:
                    deletefiles.add(filepath)
        deletefiles = list(deletefiles)

        # delete files
        num_deletes = len(deletefiles)
        logger.info('{} files will be deleted')
        for i in range(num_deletes):
            filepath = deletefiles[i]
            percent = round((i/num_deletes) * 100, 2)
            sys.stdout.write('\rCleanup Files: {}/{} - {}'.format(i, num_deletes, percent))
            logger.debug('Deleting outdated destfile: {}'.format(filepath))
            os.remove(filepath)

