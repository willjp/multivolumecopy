#!/usr/bin/env python
"""
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
import json
import logging
import os
import sys
from multivolumecopy import filesystem


# ==============
# !!DEPRECATED!!
# ==============

logger = logging.getLogger(__name__)
_jobfile = './.mvcopy-jobdata.json'
_indexfile = './.mvcopy-index'


def mvcopy_srcpaths(srcpaths, output, device_padding=None, no_progressbar=False):
    """ Copy files from under `srcpaths`, prompting for new volumes as they are filled.

    Args:
        srcpaths (list): ``(ex: ['/mnt/movies', '/mnt/music', ...])``
            A list of directories that you'd like to backup.

        output (str): ``(ex: '/mnt/backup' )``
            The directory you'd like to backup to.

    Other Parameters:
        device_padding (str, optional): ``(ex: '5G', '500M' )``
            String indicating how much empty room you'd like to leave on the
            device.

    """
    # get list of files to copy
    logger.info('Reading files to copy..')
    srcpaths = sorted([os.path.expanduser(p) for p in srcpaths])
    copyfiles = list_copyfiles(srcpaths, output)

    # write file with job info
    write_copyfiles(_jobfile, copyfiles)

    _mvcopy_files(copyfiles, output, device_padding, no_progressbar=no_progressbar)


def mvcopy_jobfile(jobfile, output, device_padding=None, index=None, no_progressbar=False):
    """ Copy files defined within `jobfile` , prompting for new volumes as they are filled.

    Args:
        output (str): ``(ex: '/mnt/backup' )``
            The directory you'd like to backup to.

    Other Parameters:
        device_padding (str, optional): ``(ex: '5G', '500M' )``
            String indicating how much empty room you'd like to leave on the
            device.

        index (int, optional): ``(ex: 540)``
            Index of the file you'd like to begin copying from
            in `jobfile` .
    """
    # get list of files to copy
    logger.info('Reading files to copy..')
    with open(jobfile, 'r') as fd:
        copyfiles = json.loads(fd.read())

    # begin copying
    _mvcopy_files(copyfiles, output, device_padding, index, no_progressbar)


def _mvcopy_files(copyfiles, output, device_padding=None, index=None, no_progressbar=False):
    """ Copies files, prompting for new device when device is full.

    Args:
        copyfiles (list):
            A list of dictionaries with information about files being copied.

        output (str):
            Directory files are being copied to.

    Other Parameters:
        device_padding (str, optional): ``(ex: '5G', '500M' )``
            String indicating how much empty room you'd like to leave on the
            device.

        index (int, optional): ``(ex: 540)``
            Index of the file you'd like to begin copying from
            in `jobfile` .
    """
    # default values
    if device_padding is None:
        device_padding = 0
    if index is None:
        index = 0

    # validation
    if not isinstance(device_padding, int):
        device_padding = filesystem.size_to_bytes(device_padding)

    # copy files
    total = len(copyfiles)
    firstindex = 0
    lastindex = 0
    while index < len(copyfiles):
        lastindex = _get_volume_lastindex(index, output, copyfiles, device_padding)
        msg = 'Destination will hold {}/{}, files starting at {}'.format(lastindex, len(copyfiles)-1, index)
        logger.info(msg)
        logger.info('Checking for/Deleting incorrect/outdated files on destination..')
        _volume_delete_extraneous(index, lastindex, copyfiles, output, no_progressbar)

        while index <= lastindex:
            copydata = copyfiles[index]
            _update_copy_progressbar(index, total, firstindex, lastindex, copydata['src'], no_progressbar)
            filesystem.copyfile(src=copydata['src'], dst=copydata['dst'])
            filesystem.copyfilestat(src=copydata['src'], dst=copydata['dst'])
            write_indexfile(_indexfile, index)
            index += 1
        _update_copy_progressbar(index, total, firstindex, lastindex, copyfiles[index - 1]['src'], no_progressbar)

        firstindex = index
        if all([
            lastindex < len(copyfiles),
            lastindex != len(copyfiles) - 1
        ]):
            _prompt_diskfull(output, index)

    # delete jobfile on completion
    if os.path.isfile(_jobfile):
        os.remove(_jobfile)
    if os.path.isfile(_indexfile):
        os.remove(_indexfile)


def _get_volume_lastindex(index, output, copyfiles, device_padding=None):
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
    if device_padding is None:
        device_padding = 0

    capacity = filesystem.avail_bytes_for_backup(output)
    capacity -= device_padding

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


def _volume_delete_extraneous(index, lastindex, copyfiles, output, no_progressbar=False):
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
    for (root, dirnames, filenames) in os.walk(output):
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
        _update_delete_progressbar(i + 1, num_deletes, filepath, no_progressbar)
        logger.debug('Deleting outdated destfile: {}'.format(filepath))
        os.remove(filepath)


def _prompt_diskfull(output, index=None):
    while True:
        print('')
        if index is not None:
            print('Next index in "{}" is: {}'.format(_jobfile, index))
        msg = 'Volume mounted to "{}" is full. Please mount a new volume, and press "c" to continue'\
                  .format(filesystem.get_mount(output))
        print(msg)
        print('(Or press "q" to abort)')
        print('')
        command = _get_user_input('> ')
        if command in ('c', 'C'):
            return
        elif command in ('q', 'Q'):
            print('Aborted by user')
            sys.exit(1)


def _update_copy_progressbar(index, total, firstindex, lastindex, srcfile, no_progressbar=False):
    """ Prints/Updates a progressbar on stdout.

    Example:

        ::
            Current Device: [####            ] 25.0%    (Job Total: [############     ] 70.12%)

    Args:
        index (int):      index of file being copied (relative to all files)
        total (int):      total number of files to be copied
        lastindex (int):  last index that will be copied to the current device before it is full
    """
    if no_progressbar:
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


def _update_delete_progressbar(index, total, filepath, no_progressbar=False):
    if no_progressbar:
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


def write_copyfiles(filepath, copyfiles):
    """ Dumps files to be copied to jsonfile.
    """
    filedir = os.path.dirname(filepath)

    if not os.path.isdir(filedir):
        os.makedirs(filedir)

    with open(filepath, 'w') as fd:
        fd.write('[\n  ')
        fd.write(',\n  '.join(json.dumps(copyfile) for copyfile in copyfiles))
        fd.write('\n]\n')


def write_indexfile(filepath, index):
    """ Dumps last completed index to file.
    """
    with open(filepath, 'w') as fd:
        fd.write(str(index))


def list_copyfiles(srcpaths, output):
    """
    Produces a list of all files that will be copied.

    Args:
        srcpaths (list):
        output (str):

    Returns:

        .. code-block:: python

            [
                {
                    'src': '/src/path',
                    'dst': '/dst/path',
                    'bytes': 1024,
                },
                ...
            ]

    """
    copyfiles = []  # [{'src': '/src/path', 'dst':'/dst/patht', 'bytes':1024}]

    for srcpath in srcpaths:
        srcpath = os.path.abspath(srcpath)

        for (root, dirnames, filenames) in os.walk(srcpath, topdown=True):
            for filename in filenames:
                filepath = os.path.abspath('{}/{}'.format(root, filename))
                relpath = filepath[len(srcpath) + 1:]
                copyfiles.append({
                    'src':      filepath,
                    'dst':      os.path.abspath('{}/{}'.format(output, relpath)),
                    'relpath':  relpath,
                    'bytes':    os.path.getsize(filepath),
                })
    copyfiles.sort(key=lambda x: x['src'])

    return copyfiles


def _get_user_input(msg):
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


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG, format='%(levelname)s| %(msg)s')
    if not os.path.isdir('/var/tmp/qtconfigs'):
        os.makedirs('/var/tmp/qtconfigs')
    mvcopy_srcpaths(['~/.config/qutebrowser'], '/var/tmp/qtconfigs')
    #_prompt_diskfull('/home/will')
