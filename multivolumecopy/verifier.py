import os
from multivolumecopy import filesystem
from multivolumecopy.resolvers import jobfileresolver


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
        different_indexes = self._find_files_different(device_start_index, last_copied_index)
        missing_indexes = self._find_files_missing(device_start_index, last_copied_index)
        copied_bytes = self._get_expected_copy_size(device_start_index, last_copied_index)

        results = VerifyResults(self.copyfiles, self.options)
        results.device_capacity_bytes = capacity_bytes
        results.backup_bytes = backup_bytes
        results.copied_bytes = copied_bytes
        results.different_indexes = different_indexes
        results.missing_indexes = missing_indexes
        return results

    def _find_files_different(self, device_start_index, last_copied_index):
        different = []
        kwargs = dict(mtime=self.options.compare_mtime,
                      size=self.options.compare_size,
                      checksum=self.options.compare_checksum)
        for copyfile in self.copyfiles[device_start_index:last_copied_index]:
            if not os.path.isfile(copyfile.src):
                continue
            if not os.path.isfile(copyfile.dst):
                continue
            if filesystem.files_different(copyfile.src, copyfile.dst, **kwargs):
                different.append(copyfile.index)
        return different

    def _find_files_missing(self, device_start_index, last_copied_index):
        missing = []
        for copyfile in self.copyfiles[device_start_index:last_copied_index]:
            if not os.path.isfile(copyfile.dst):
                # we can't copy src if it does not exist
                if not os.path.isfile(copyfile.src):
                    continue
                missing.append(copyfile.index)
        return missing

    def _get_expected_copy_size(self, device_start_index, last_copied_index):
        """ Returns sum of sizes from all files successfully copied.
        """
        size = 0
        for copyfile in self.copyfiles[device_start_index:last_copied_index]:
            size += copyfile.bytes
        return size


class VerifyResults(object):
    """ Stores/Formats Verify results into a report.
    """
    def __init__(self, copyfiles, options):
        self.copyfiles = copyfiles
        self.options = options
        self.device_capacity_bytes = 0
        self.backup_bytes = 0
        self.copied_bytse = 0
        self.different_indexes = []
        self.missing_indexes = []

    def format(self):
        """ Generates a report of a volume's backup, with the goal of identifying issues.
        """
        msg = '======== SUMMARY ========\n'
        msg += 'VOLUME SIZE:    [{:<5}] {}\n'.format(
            filesystem.format_size(self.device_capacity_bytes, self.options.size_unit),
            filesystem.format_size(self.device_capacity_bytes, 'B'),
        )
        msg += 'BACKUP SIZE:    [{:<5}] {}\n'.format(
            filesystem.format_size(self.backup_bytes, self.options.size_unit),
            filesystem.format_size(self.backup_bytes, 'B'),
        )
        msg += 'EXPECTED SIZE:  [{:<5}] {}\n'.format(
            filesystem.format_size(self.copied_bytes, self.options.size_unit),
            filesystem.format_size(self.copied_bytes, 'B'),
        )
        msg += '=========================\n'

        if self.different_indexes or self.missing_indexes:
            msg += '=================== WARNING ===================\n'
            msg += '- differences between backup and source detected '

            if self.different_indexes:
                msg += 'DIFFERENT:\n'
                for index in self.different_indexes:
                    data = self.copyfiles[index]
                    msg += '  [{}]\n    {}\n    {}\n'.format(data.index, data.src, data.dst)

            if self.missing_indexes:
                msg += '\n'
                msg += 'MISSING:\n'
                for index in self.missing_indexes:
                    data = self.copyfiles[index]
                    msg += '  [{}]\n    {}\n    {}\n'.format(data.index, data.src, data.dst)
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


