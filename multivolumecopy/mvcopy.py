#!/usr/bin/env python
"""
Rsync wrapper to facilitate quick n' dirty multi-HDD backups of a file-server.
"""
# builtin
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
import os
import sys
import logging
# package
# external
# internal
from multivolumecopy import filesystem


# TODO: if insufficient room for single-file, request next volume instead of exception


logger = logging.getLogger(__name__)


def mvcopy(srcpaths, output, device_padding=None):
    """ copy files from srcpaths to output, spanning multiple volumes (HDDs, tapes, etc.).
    HDD must be formatted and mounted in order to be used.

     .. warning::

         Backup Volume size cannot exceed python's :py:obj`sys.maxsize`
         in bytes. This works out to be 8589934592 TB.

    Args:
        srcpaths (list): ``(ex: ['/mnt/movies', '/mnt/music', ...])``
            A list of directories that you'd like to backup.

        output (str): ``(ex: '/mnt/backup' )``
            The directory you'd like to backup to.

    Other Parameters:
        device_padding (str, int, optional): ``(ex: 1024, '10G', '5M', ..)``
            Room to leave empty on the output device (HDD, dvd, etc)
            before prompting user to insert new backup media.
    """
    # defaults
    if device_padding is None:
        device_padding = 0

    srcpaths = sorted([os.path.expanduser(p) for p in srcpaths])

    # validation
    if not isinstance(device_padding, int):
        device_padding = filesystem.size_to_bytes(device_padding)

    # copy
    index = 0
    copyfiles = list_copyfiles(srcpaths, output)

    while index < len(copyfiles):
        lastindex = _get_volume_lastindex(index, output, copyfiles, device_padding)
        _volume_delete_extraneous(index, lastindex, copyfiles, output)

        while index <= lastindex:
            copydata = copyfiles[index]
            filesystem.copyfile(src=copydata['src'], dst=copydata['dst'])
            filesystem.copyfilestat(src=copydata['src'], dst=copydata['dst'])
            index += 1

        if all([
            lastindex < len(copyfiles),
            lastindex != len(copyfiles) - 1
        ]):
            _prompt_diskfull(output)


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


def _volume_delete_extraneous(index, lastindex, copyfiles, output):
    """
    Produces a list of all destfiles that will exist in `output` for
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

    # delete all files that are not from this list of srcfiles
    for (root, dirnames, filenames) in os.walk(output):
        for filename in filenames:
            filepath = os.path.abspath('{}/{}'.format(root, filename))

            if filepath not in dstfiles:
                os.remove(filepath)


def _prompt_diskfull(output):
    while True:
        print('')
        print(
            'Volume mounted to "{}" is full. Please mount a new volume, and press "c" to continue'.format(
                filesystem.get_mount(output)
            )
        )
        print('(Or press "q" to abort)')
        print('')
        command = str(input('> '))
        if command in ('c', 'C'):
            return
        elif command in ('q', 'Q'):
            print('Aborted by user')
            sys.exit(1)


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

    return copyfiles


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG, format='%(levelname)s| %(msg)s')
    mvcopy(['~/.config/qutebrowser'], '/var/tmp/qtconfigs')
