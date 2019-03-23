#!/usr/bin/env python
"""
Rsync wrapper to facilitate quick n' dirty multi-HDD backups of a file-server.
"""
# builtin
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
import json
import logging
import os
import sys
# package
# external
# internal
from multivolumecopy import filesystem


logger = logging.getLogger(__name__)
_jobfile = './mvcopy-jobdata.json'


def mvcopy_srcpaths(srcpaths, output, device_padding=None):
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

    _mvcopy_files(copyfiles, output, device_padding)


def mvcopy_jobfile(jobfile, output, device_padding=None, index=None):
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
    _mvcopy_files(copyfiles, output, device_padding, index)


def _mvcopy_files(copyfiles, output, device_padding=None, index=None):
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
    while index < len(copyfiles):
        lastindex = _get_volume_lastindex(index, output, copyfiles, device_padding)
        logger.info('Destination will hold {}/{}, files starting at {}'.format(
            lastindex, len(copyfiles)-1, index
        ))
        logger.info('Checking for/Deleting incorrect/outdated files on destination..')
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
            _prompt_diskfull(output, index)

    # delete jobfile on completion
    if os.path.isfile(_jobfile):
        os.remove(_jobfile)


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
                logger.debug('Deleting outdated destfile: {}'.format(filepath))
                os.remove(filepath)


def _prompt_diskfull(output, index=None):
    while True:
        print('')
        if index is not None:
            print('Current index in "{}" is: {}'.format(_jobfile, index))
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


def write_copyfiles(filepath, copyfiles):
    filedir = os.path.dirname(filepath)

    if not os.path.isdir(filedir):
        os.makedirs(filedir)

    with open(filepath, 'w') as fd:
        fd.write('[\n  ')
        fd.write(',\n  '.join(json.dumps(copyfile) for copyfile in copyfiles))
        fd.write('\n]\n')


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
    if not os.path.isdir('/var/tmp/qtconfigs'):
        os.makedirs('/var/tmp/qtconfigs')
    mvcopy_srcpaths(['~/.config/qutebrowser'], '/var/tmp/qtconfigs')
    #_prompt_diskfull('/home/will')
