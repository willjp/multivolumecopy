#!/usr/bin/env python
"""
Tools for working with files/filesystem.
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
import logging
import os
import re
import shutil


logger = logging.getLogger(__name__)
_UNIT_TO_BYTES = (
    (('T', 'TB'), 1000000000000),
    (('G', 'GB'), 1000000000),
    (('M', 'MB'), 1000000),
    (('K', 'KB'), 1000),
    (('B', ''), 1),
)


def size_to_bytes(size):
    """ Converts a string representation of a unit to a size in bytes.

    Args:
        size (str): ``(ex: '6T', '5M', '10G', '6K', '8B', '8' )``
            The size you'd like to convert to bytes. (if no unit, assumes bytes).

    Returns:
        int: a size in bytes
    """
    size = str(size)
    unit_to_bytes = dict(_UNIT_TO_BYTES)
    match = re.search('[a-zA-Z]+$', size)
    if match:
        unit = match.group()
        size = int(size[:-1 * len(unit)])
    else:
        size = int(size)
        unit = 'B'

    for units in unit_to_bytes:
        if unit in units:
            multiplier = unit_to_bytes[units]
            break
    else:
        raise NotImplementedError('Unable to identify unit: {}'.format(unit))

    return size * multiplier


def bytes_to_unit(size, unit):
    """ Converts an integer of bytes to the unit of your choosing.

    Args:
        size (int): ``(ex: 100)``
        unit (str): ``(ex: 'M' 'MB' 'TB')``
    Returns:
        float: size in unit of your choosing.
    """
    for i in range(len(_UNIT_TO_BYTES)):
        units = _UNIT_TO_BYTES[i][0]
        if unit in units:
            return size / _UNIT_TO_BYTES[i][1]
    raise NotImplementedError('Unrecognized Unit: {}'.format(unit))


def format_size(size, unit, round_by=2):
    """ Produces string with size in bytes expressed as a unit.

    Args:
        size (int): ``(ex: 100)``
        unit (str): ``(ex: 'M' 'MB' 'TB')``
    Returns:
        str: ``(ex: '10G')``
    """
    size_in_unit = bytes_to_unit(size, unit)
    if round_by > 0:
        return '{}{}'.format(round(size_in_unit, round_by), unit)
    return '{}{}'.format(int(size_in_unit), unit)


def volume_capacity(output):
    """ Obtains the total size of volume (on which directory `output` resides).

    Returns:
        int: size in bytes
    """
    statvfs = os.statvfs(output)
    avail_bytes = statvfs.f_blocks * statvfs.f_frsize

    return avail_bytes


def volume_free(output):
    """ Obtains available bytes on the volume (on which directory `output` resides).

    Returns:
        int: size in bytes
    """
    # get free space left on volume
    statvfs = os.statvfs(output)
    avail_bytes = statvfs.f_bavail * statvfs.f_frsize

    return avail_bytes


# TODO DELETE ME
def backup_bytes(output):
    """ Obtains the total size occupied by the files under provided directory `output` .

    Returns:
        int: size in bytes
    """
    # get total size occupied by the current output files
    backup_bytes = 0
    for (root, dirnames, filenames) in os.walk(output):
        for dirname in dirnames:
            backup_bytes += os.path.getsize('{}/{}'.format(root, dirname))

        for filename in filenames:
            backup_bytes += os.path.getsize('{}/{}'.format(root, filename))

    return backup_bytes


def directory_size(directory):
    """ Returns total size of all files in directory in bytes.
    """
    # get total size occupied by the current output files
    total_bytes = 0
    for (root, dirnames, filenames) in os.walk(directory):
        for dirname in dirnames:
            dirpath = '{}/{}'.format(root, dirname)
            if os.path.islink(dirpath):
                total_bytes += os.lstat(dirpath).st_size
            else:
                total_bytes += os.path.getsize(dirpath)

        for filename in filenames:
            filepath = '{}/{}'.format(root, filename)
            if os.path.islink(filename):
                total_bytes += os.lstat(filepath).st_size
            else:
                total_bytes += os.path.getsize(filepath)

    return total_bytes


# TODO DELETE ME
def avail_bytes_for_backup(output):
    """ Determines how much room is available for the backup, disregarding size of files in backup-dir (in bytes).

    Returns:
        int: size in bytes
    """
    # add volume free-space to total backup bytes used.
    return volume_capacity(output) + backup_bytes(output)


def get_mount(filepath):
    """ Returns the highest-level directory a file's filesystem is mounted to.

    Args:
        filepath (str): ``(ex: '/mnt/movies/amelie/amelie.mkv')``
            path to a file or directory

    Returns:
        str: ``(ex: '/mnt/movies')``
            the mountpoint of the filesystem.
    """
    path = os.path.abspath(filepath)
    while not os.path.ismount(path):
        if os.path.dirname(path) == path:
            raise RuntimeError('file is not on a mounted filesystem: "{}"'.format(filepath))
        path = os.path.dirname(path)

    return path


def files_different(file_a, file_b, mtime=True, size=True, checksum=False):
    """ Returns ``True`` if the provided files are not the same.

    Args:
        file_a (str): path to the first file.
        file_b (str): path to the second file.
        mtime (bool, optional): Compare the last-modified dates
        size (bool, optional): Compare the file-sizes
        checksum (bool, optional): Compare the file checksums (slow).

    Returns:
        bool: True if files are different.
    """
    checks = []
    checkmsg = []
    if mtime:
        # reporting differences despite repr of float being equal
        checks.append(int(os.path.getmtime(file_a)) != int(os.path.getmtime(file_b)))
        checkmsg.append('mod-time')

    if size:
        checks.append(os.path.getsize(file_a) == os.path.getsize(file_b))
        checkmsg.append('size')

    if checksum:
        checkmsg.append('checksum')
        raise NotImplementedError('todo')

    return all(checks)


def copyfile(src, dst, reraise=True, log_errors=True):
    """ Copies a single file, if it needs copying.

    Args:
        src (str): ``(ex: '/src/file.txt')
            file to copy

        dst (str): ``(ex: '/dst/file.txt')``
            copy file to

    Returns:
        bool: True if a file was copied.
    """
    if os.path.isfile(dst):
        if not files_different(src, dst):
            logger.debug('file exists, same mod-date/size. skipped: "{}"'.format(dst))
            return False

    # make directories, and copy file
    try:
        dstdir = os.path.dirname(dst)
        try:
            os.makedirs(dstdir)
        except(FileExistsError):
            pass
        logger.debug('copying file: "{}" to "{}"'.format(src, dst))
        shutil.copyfile(src, dst)
        return True
    except(OSError):
        if os.path.isfile(dst):
            os.remove(dst)
        if log_errors:
            logger.error('Unable to copy "{}" to "{}"'.format(src, dst))
        if reraise:
            raise

    return False


def copyfilestat(src, dst):
    """ Copy permissions, access-time, modification-time, ACLs from
    srcfile to dstfile (including all parent directories in relpath).

    Args:
        src (str): ``(ex: '/src/path/file.txt')``
            file to copy

        dst (str): ``(ex: '/dst/path/file.txt')``
            location to copy to
    """
    src = src.replace('\\', '/')
    dst = dst.replace('\\', '/')

    relpath = common_relpath(src, dst)

    # get src/dst root
    dstroot = dst[: -1 * (len(relpath) + 1)]
    srcroot = src[: -1 * (len(relpath) + 1)]

    # copystat for each directory + the file
    srcpath = srcroot
    dstpath = dstroot
    for part in relpath.split('/'):
        srcpath += '/{}'.format(part)
        dstpath += '/{}'.format(part)
        try:
            shutil.copystat(srcpath, dstpath)
        except(Exception):
            logger.warning('Unable to copy stats from "{}"'.format(src))


def common_relpath(path_a, path_b):
    """ Returns common end-path for two identical
    filepaths with different root-directories.

    Args:
        path_a (str): ``(ex: '/path/src/neat/file.txt')``
        path_b (str): ``(ex: '/another/path/dst/neat/file.txt')``

    Returns:
        str: ``'neat/file.txt'``
    """
    path_a = path_a.replace('\\', '/')
    path_b = path_b.replace('\\', '/')

    # nothing to do. same file.
    if path_a == path_b:
        return

    # get relpath
    relpath = ''
    for i in range(len(path_a)):
        index = (i * -1) - 1  # value should never be zero
        if path_a[index] != path_b[index]:
            break
        relpath = path_a[index] + relpath

    while relpath.startswith('/'):
        relpath = relpath[1:]

    return relpath


if __name__ == '__main__':
    logging.basicConfig()
    logging.root.level = logging.DEBUG

    capacity = volume_capacity(os.path.abspath('.'))
    copyfile('/home/will/.bashrc', '/var/tmp/.bashrc')

    copyfilestat('/home/will/.bashrc', '/var/tmp/.bashrc')
