from multivolumecopy.reconcilers import reconciler
from multivolumecopy import filesystem
import os


class KeepFilesReconciler(reconciler.Reconciler):
    """ Estimates disk/dir capacity, attempting to keep files that will be part
    of the copy job with identical modified-at/size metadata.

    Notes:
        * assumes queue order matches copyfiles list.
    """
    def __init__(self, source, options):
        super(KeepFilesReconciler, self).__init__(source, options)

    def reconcile(self, copyfiles, copied_indexes):
        self._remove_unrelated_or_copied_paths(copyfiles, copied_indexes)
        self._remove_copypaths_that_wont_fit(copyfiles, copied_indexes)

    def _remove_unrelated_or_copied_paths(self, copyfiles, copied_indexes):
        # remove files unassociated with backup
        unrelated_files = self._get_unrelated_files(copyfiles, copied_indexes)
        for filepath in unrelated_files:
            os.remove(filepath)

    def _remove_copypaths_that_wont_fit(self, copyfiles, copied_indexes):
        # after unassociated paths have been removed,
        # we can estimate the available bytes using (volume-size + output-size)
        # then use that to determine/delete files that will not fit in backup.
        # (cannot be 100% accurate, due to filesystem features/compression)
        avail_bytes = self._estimate_available_bytes()
        target_indexes = self._estimate_targets(avail_bytes, copyfiles, copied_indexes)
        purge_indexes = [i for i in range(len(copyfiles)) if i not in copied_indexes and i not in target_indexes]
        for i in purge_indexes:
            dstfile = copyfiles[i]['dst']
            if os.path.isfile(dstfile):
                os.remove(dstfile)

    def _get_unrelated_files(self, copyfiles, copied_indexes):
        # catches both files that have alread been copied (`copied_indexes`)
        # and files that have nothing to do with our copy job.
        unrelated_files = set()
        uncopied_dstfiles = [copyfiles[i]['dst'] for i in range(len(copyfiles)) if i not in copied_indexes]

        for (root, dirnames, filenames) in os.walk(self.options.output):
            for filename in filenames:
                filepath = os.path.abspath('{}/{}'.format(root, filename))
                if filepath in uncopied_dstfiles:
                    continue
                unrelated_files.add(filepath)
        return unrelated_files

    def _estimate_available_bytes(self):
        if os.path.isdir(self.options.output):
            dir_size = filesystem.directory_size(self.options.output)
        else:
            dir_size = 0
        volume_size = filesystem.volume_capacity(self.options.output)
        return volume_size + dir_size

    def _estimate_targets(self, avail_bytes, copyfiles, copied_indexes):
        """ Return a list of copyfiles we think will fit on the curent volume.
        """
        target_indexes = []
        uncopied_indexes = [i for i in range(len(copyfiles)) if i not in copied_indexes]
        backup_bytes = 0
        for i in uncopied_indexes:
            copyfile = copyfiles[i]
            if (backup_bytes + copyfile['bytes']) >= avail_bytes:
                return target_indexes
            target_indexes.append(i)
            backup_bytes += copyfile['bytes']
        return target_indexes
