import os
from multivolumecopy import filesystem
from multivolumecopy.resolvers import jobfileresolver


class VerifyResults(object):
    def __init__(self, copyfiles):
        self.copyfiles = copyfiles
        self.device_capacity_bytes = 0
        self.backup_bytes = 0
        self.copied_bytse = 0
        self.different_indexes = []
        self.missing_indexes = []

    def format(self):
        """ Generates a report of a volume's backup, with the goal of identifying issues.
        """
        msg =  '======== SUMMARY ========\n'
        msg += 'DEVICE SIZE: {}\n'.format(self.device_capacity_bytes)
        msg += 'BACKUP SIZE: {}\n'.format(self.backup_bytes)
        msg += 'COPIED_SIZE: {}\n'.format(self.copied_bytes)
        msg += '=========================\n'

        if different_indexes or missing_indexes:
            msg += '=================== WARNING ===================\n'
            msg += '- differences between backup and source detected '

            if different_indexes:
                msg += 'DIFFERENT:\n'
                for index in self.different_indexes:
                    data = self.copyfiles[index]
                    msg += '  [{}]\n    {}\n    {}'\n.format(data.index, data.src, data.dst)

            if missing_indexes:
                msg += '\n'
                msg += 'MISSING:\n'
                for index in self.missing_indexes:
                    data = self.copyfiles[index]
                    msg += '  [{}]\n    {}\n    {}'\n.format(data.index, data.src, data.dst)
            msg += '===============================================\n'

        return msg

    def valid(self):
        """ Quick n' dirty, does this look valid?
        """
        if self.different_indexes:
            return False
        if self.missing_indexes:
            return False
        return True


class Verifier(object):
    """ Verifies a portion of a backup written to a single volume.
    Ex volume 3 of 5 involved in a backup.
    """
    def __init__(self, resolver, options):
        self.resolver = resolver
        self.options = options
        self.copyfiles = tuple()

    def verify(self, device_start_index, last_copied_index):
        self.copyfiles = self.resolver.get_copyfiles(device_start_index)

        capacity_bytes = filesystem.volume_capacity(self.options.output)
        backup_bytes = filesystem.directory_size(self.options.output)
        different_indexes = self._find_files_different(last_copied_index)
        missing_indexes = self._find_files_missing(last_copied_index)
        copied_bytes = self._get_copied_size(missing_indexes, different_indexes)

        results = VerifyResults(self.copyfiles)
        results.device_capacity_bytes = capacity_bytes
        results.backup_bytes = backup_bytes
        results.copied_bytes = copied_bytes
        results.different_indexes = different_indexes
        results.missing_indexes = missing_indexes
        return results

    def _find_files_different(self, last_copied_index):
        different = []
        kwargs = dict(mtime=self.options.compare_mtime,
                      size=self.options.compare_size,
                      checksum=self.options.compare_checksum)
        for copyfile in self.copyfiles[:last_copied_index]:
            if filesystem.files_different(copyfile.src, copyfile.dst, **kwargs):
                different.append(copyfile.index)
        return missing

    def _find_files_missing(self, last_copied_index):
        missing = []
        for copyfile in self.copyfiles[:last_copied_index]:
            if not os.path.isfile(copyfile.dst):
                missing.append(copyfile.index)
        return missing

    def _get_copied_size(self, missing_indexes, different_indexes):
        """ Returns sum of sizes from all files successfully copied.
        """
        size = 0
        i = 0
        for copyfile in self.copyfiles:
            if i in missing_indexes:
                continue
            if i in different_indexes:
                continue
            size += copyfile.size
        return size


