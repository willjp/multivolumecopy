from multivolumecopy.copiers import copier
from multivolumecopy import filesystem, copyoptions
import json
import logging
import os
import sys


logger = logging.getLogger(__name__)


# =========================
# TODO: DEPRECATED - DELETE
# =========================


# TODO: split class up -- SRP
#       LastIndexCalculator


class SimpleCopier(copier.Copier):
    """ V1 copier.

    .. warning::
        Messy, needs to be split for SRP, memory issues with python-3.7.
        This needs rewritten badly.

    """
    def __init__(self, source, options=None):
        """
        Args:
            source (CopySource):
                CopySource object, determines files to be copied.

            output (str): ``(ex: '/mnt/backup' )``
                The directory you'd like to backup to.

            options (CopyOptions, None):
                Options to use while performing copy
        """
        super(SimpleCopier, self).__init__(source, options)

    def start(self):
        """ Copies files, prompting for new device when device is full.
        """
        copyfiles = self.source.get_copyfiles()

        # defaults
        index = self.options.start_index

        # copy files
        total = len(copyfiles)
        index = device_firstindex = 0
        lastindex = 0
        while index < len(copyfiles):
            lastindex = self._get_volume_lastindex(index, copyfiles)
            msgdata = {'lastindex': lastindex, 'totalindex': len(copyfiles)-1, 'index': index}
            logger.info('Destination holds {lastindex}/{totalindex}, '
                        'files starting at {index}'.format(**msgdata))
            logger.info('Checking for/Deleting incorrect/outdated files on destination..')
            self._volume_delete_extras(index, lastindex, copyfiles)
            index = self._copy_index_range(copyfiles, index, lastindex, device_firstindex, total)

            device_firstindex = index
            if lastindex < len(copyfiles) -1:
                self._prompt_diskfull(index)

        # delete jobfile on completion
        self._deletefile(self.options.jobfile)
        self._deletefile(self.options.indexfile)

    def _copy_index_range(self, copyfiles, first, last, device_firstindex, total):
        """
        Returns:
            int: the next index that needs processing.
        """
        index = first
        while index <= last:
            copydata = copyfiles[index]
            self._update_copy_progressbar(index, total, device_firstindex, last, copydata['src'])

            # if copy fails, repeat it for next device
            try:
                filesystem.copyfile(src=copydata['src'], dst=copydata['dst'])
            except(OSError):
                return index

            filesystem.copyfilestat(src=copydata['src'], dst=copydata['dst'])
            self.write_indexfile(index)
            index += 1
        self._update_copy_progressbar(index, total, device_firstindex, last, copyfiles[index - 1]['src'])
        # -1, since last iteration is either a fail, or one above last.
        return index

    def _deletefile(self, filepath):
        if not os.path.isfile(filepath):
            return False
        os.remove(filepath)
        return True

    def _volume_delete_extras(self, index, lastindex, copyfiles):
        """ Produces a list of all destfiles that will exist in `output` for
        this volume, and deletes all other files.

        Args:
            index (int):
                First `copyfiles` index to be copied to volume.

            lastindex (int):
                Last `copyfiles` index to be copied to volume.
        """
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
            self._update_delete_progressbar(i + 1, num_deletes, filepath)
            logger.debug('Deleting outdated destfile: {}'.format(filepath))
            os.remove(filepath)

    def _update_copy_progressbar(self, index, total, firstindex, lastindex, srcfile):
        """ Prints/Updates a progressbar on stdout.

        Example:

            ::
                Current Device: [####            ] 25.0%    (Job Total: [############     ] 70.12%)

        Args:
            index (int):      index of file being copied (relative to all files)
            total (int):      total number of files to be copied
            lastindex (int):  last index that will be copied to the current device before it is full
        """
        if not self.options.show_progressbar:
            return

        total_progress = (index / total) * 100

        device_index = index - firstindex
        device_total = lastindex - firstindex

        if device_total == 0:
            # device total is 0 if only a single file is being copied
            device_total = 1

        if (device_index - 1) < 0:
            # firstindex > lastindex when updating total to 100%
            # (progress is printed before AND after operation)
            device_progress = 0
        else:
            device_progress = (device_index / device_total) * 100
        if device_progress > 100:
            device_progress = 100

        completed_steps = int(device_progress / 4)  # 25 steps-per-progressbar
        uncompleted_steps = 25 - completed_steps

        if len(srcfile) < 50:
            print_filepath = srcfile
        else:
            print_filepath = '...' + srcfile[-50:]

        sys.stdout.write(
            '\r(Total: {}/{} {}%) Device: {}/{} {}% [{}{}]   {} '.format(
                # total
                index,
                total,
                round(total_progress, 2),
                # device
                device_index if device_index <= device_total else device_index - 1,
                device_total,
                round(device_progress, 2),
                # progress
                '#' * completed_steps,
                ' ' * uncompleted_steps,
                print_filepath,
            )
        )
        sys.stdout.flush()

        # write newline when job complete (so future \r prints get their own line)
        if device_progress >= 100:
            sys.stdout.write('\n')

    def _update_delete_progressbar(self, index, total, filepath):
        if not self.options.show_progressbar:
            return

        progress = (index / total) * 100
        completed_steps = int(progress / 4)  # 25 steps-per-progressbar
        uncompleted_steps = 25 - completed_steps

        if len(filepath) < 50:
            print_filepath = filepath
        else:
            print_filepath = '...' + filepath[-50:]

        sys.stdout.write(
            '\r(Deleting Non-Backup Files {}/{} {}%): [{}{}]    {}'.format(
                index,
                total,
                round(progress, 2),
                '#' * completed_steps,
                ' ' * uncompleted_steps,
                print_filepath,
            )
        )

        # write newline when job complete (so future \r prints get their own line)
        if progress >= 100:
            sys.stdout.write('\n')

    def _prompt_diskfull(self, index=None):
        while True:
            print('')
            if index is not None:
                print('Next index in "{}" is: {}'.format(self.options.jobfile, index))
            msg = 'Volume mounted to "{}" is full. Please mount a new volume, and press "c" to continue'\
                      .format(filesystem.get_mount(self.options.output))
            print(msg)
            print('(Or press "q" to abort)')
            print('')
            command = self._get_user_input('> ')
            if command in ('c', 'C'):
                return
            elif command in ('q', 'Q'):
                print('Aborted by user')
                sys.exit(1)

    def _get_user_input(self, msg):
        """ Request user input, convert reply to native string type.

        Args:
            msg (str):
                Message you'd like to present at user-input prompt.

        Returns:
            str: characters typed by user.
        """
        if sys.version_info[0] < 3:
            reply = raw_input(msg)
            return reply.encode('utf-8')
        else:
            reply = input(msg)
            if hasattr(reply, 'decode'):
                return reply.decode('utf-8')
            else:
                return reply

    def _get_volume_lastindex(self, index, copyfiles):
        """ Get the index of the last file that will fit on the
        current volume.

        Args:
            copyfiles (list):
                The list of all files to be copied

            index (int):
                The index of the first file to be copied
                on this volume.

        Return:
            .. code-block:: python

                143
        """
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


