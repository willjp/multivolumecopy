import logging
import os
from multivolumecopy import filesystem
from multivolumecopy.resolvers import jobfileresolver


logger = logging.getLogger(__name__)


class Verifier(object):
    """ Verifies a portion of a backup written to a single volume.
    Ex volume 3 of 5 involved in a backup.
    """
    def __init__(self, resolver, options):
        """ Constructor.

        Args:
            resolver (multivolumecopy.resolvers.resolver.Resolver):
                produces list of copyfiles.

            options (multivolumecopy.copyoptions.CopyOptions):
                options used for copyjob.
        """
        self.resolver = resolver
        self.options = options
        self.copyfiles = tuple()

    def verify(self, device_start_index, last_copied_index):
        """

        Args:
            device_start_index (int):
                index of first file to be copied on mounted device.

            last_copied_index (int):
                last index to be copied onto mounted device (estimate).

        Returns:
            VerifyResults:
                object with info about the results.
        """
        self.copyfiles = self.resolver.get_copyfiles(device_start_index)

        capacity_bytes = filesystem.volume_capacity(self.options.output)
        backup_bytes = filesystem.directory_size(self.options.output)
        different_indexes = self._find_files_different(device_start_index, last_copied_index)
        missing_indexes = self._find_files_missing(device_start_index, last_copied_index)
        copied_bytes = self._get_expected_copy_size(device_start_index,
                                                    last_copied_index,
                                                    missing_indexes)

        results = VerifyResults(self.copyfiles, self.options)
        results.device_capacity_bytes = capacity_bytes
        results.backup_bytes = backup_bytes
        results.copied_bytes = copied_bytes
        results.different_indexes = different_indexes
        results.missing_indexes = missing_indexes
        return results

    def _find_files_different(self, device_start_index, last_copied_index):
        """ Find files that need to be copied.
        """
        different = []
        kwargs = dict(mtime=self.options.compare_mtime,
                      size=self.options.compare_size,
                      checksum=self.options.compare_checksum)
        for copyfile in self.copyfiles[device_start_index:last_copied_index]:
            if not os.path.isfile(copyfile.src):
                continue

            if not os.path.isfile(copyfile.dst):
                different.append(copyfile.index)
            elif filesystem.files_different(copyfile.src, copyfile.dst, **kwargs):
                different.append(copyfile.index)

        return different

    def _find_files_missing(self, device_start_index, last_copied_index):
        """ Finds src-files that are not present.
        """
        missing = []
        for copyfile in self.copyfiles[device_start_index:last_copied_index]:
            if not os.path.isfile(copyfile.dst):
                # we can't copy src if it does not exist
                if not os.path.isfile(copyfile.src):
                    continue
                missing.append(copyfile.index)
        return missing

    def _get_expected_copy_size(self, device_start_index, last_copied_index, missing_indexes):
        """ Returns sum of sizes from all files successfully copied.
        """
        size = 0
        for i in range(device_start_index, last_copied_index):
            # exclude src-files that are missing - they will not be included in backup
            if i in missing_indexes:
                continue
            copyfile = self.copyfiles[i]
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
        self.copied_bytes = 0
        self.different_indexes = []
        self.missing_indexes = []

    def format(self):
        """ Generates a report of a volume's backup, with the goal of identifying issues.
        """
        warnings = []
        checks = []
        msg = '=================== SUMMARY ===================\n'
        msg += '  VOLUME SIZE:    [{:<5}] {}\n'.format(
            filesystem.format_size(self.device_capacity_bytes, self.options.size_unit),
            filesystem.format_size(self.device_capacity_bytes, 'B'),
        )
        msg += '  BACKUP SIZE:    [{:<5}] {}\n'.format(
            filesystem.format_size(self.backup_bytes, self.options.size_unit),
            filesystem.format_size(self.backup_bytes, 'B'),
        )
        msg += '  EXPECTED SIZE:  [{:<5}] {}\n'.format(
            filesystem.format_size(self.copied_bytes, self.options.size_unit),
            filesystem.format_size(self.copied_bytes, 'B'),
        )
        msg += '\n'

        # check files exist
        checks, warnings = self._format_check_all_files_exist(checks, warnings)
        checks, warnings = self._format_check_copied_matches_expectated(checks, warnings)

        # format checks
        if checks:
            msg += '==================== CHECKS ===================\n'
            msg += '  ' + '\n  '.join(checks) + '\n\n'

        if warnings:
            msg += '=================== WARNING ===================\n'
            msg += '  ' + '\n  '.join(warnings) + '\n'
        msg += '===============================================\n'

        return msg

    def _format_check_all_files_exist(self, checks, warnings):
        if self.different_indexes or self.missing_indexes:
            checks.append('[ ] all expected files backed up')

            warn = ''
            if self.different_indexes:
                warn += 'DIFFERENT:\n'
                for index in self.different_indexes:
                    data = self.copyfiles[index]
                    warn += '  [{}]\n    {}\n    {}\n'.format(data.index, data.src, data.dst)

            if self.missing_indexes:
                warn += 'MISSING:\n'
                for index in self.missing_indexes:
                    data = self.copyfiles[index]
                    warn += '  [{}]\n    {}\n    {}\n'.format(data.index, data.src, data.dst)
            warnings.append(warn)
        else:
            checks.append('[x] all expected files backed up')
        return checks, warnings

    def _format_check_copied_matches_expectated(self, checks, warnings):
        if self.backup_bytes > self.copied_bytes:
            checks.append('[ ] expected size roughly matches backup size')
            warn = '- (backup-size > expected) This may indicate that files exist in output that are not related to backup\n'
            warnings.append(warn)
        else:
            checks.append('[x] expected size roughly matches backup size')
        return checks, warnings

    def valid(self):
        """ Quick n' dirty, does this look valid?
        """
        if self.different_indexes:
            return False
        if self.missing_indexes:
            return False
        return True


