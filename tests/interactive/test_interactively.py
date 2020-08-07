#!/usr/bin/env python
import os
import platform
import shutil
import subprocess
import sys


class InteractiveTestWithDiskRequest:
    """ Creates files/disks and runs a real copy 
    including a single disk rollover (request for new disk).

    When a new disk is requested, you'll need to manually

    ::

        sudo umount -f build/mnt
        sudo mount build/test/disk2.img build/mnt

        # press 'c' to continue

    """
    # directories
    root = 'build/test'
    mnt = 'build/mnt'

    def __init__(self):
        # 2x 5M disks
        self.disk_1 = Disk('{}/disk1.img'.format(self.root))
        self.disk_2 = Disk('{}/disk2.img'.format(self.root))

        # 7x 1M files
        self.files = [File('{}/files/{}'.format(self.root, i)) for i in range(7)]

    def perform(self):
        try:
            self._prepare()
            cmds = ['python', 'build/lib/multivolumecopy', '{}/files/'.format(self.root), '--output', self.mnt]
            subprocess.call(cmds, universal_newlines=True)
        finally:
            self._cleanup()

    def _cleanup(self):
        operations = []
        operations.append(lambda: subprocess.check_call(['sudo', 'umount', self.mnt], universal_newlines=True))
        operations.extend([lambda: x.delete for x in self.files])
        operations.extend([lambda: x.delete for x in [self.disk_1, self.disk_2]])
        for operation in operations:
            try:
                operation()
            except:
                pass

    def _prepare(self):
        self._cleanup()

        # create empty mount dirs
        for dir_ in [self.root, '{}/files'.format(self.root), self.mnt]:
            if os.path.isdir(dir_):
                shutil.rmtree(dir_)
            os.makedirs(dir_)

        # create disks
        for disk in [self.disk_1, self.disk_2]:
            disk.create()
            disk.format()

        # mount first disk
        self.disk_1.mount(self.mnt)

        # create files
        for file_ in self.files:
            file_.create()


class Filesystem:
    """ Helper for determining/formatting disks with a filesystem appropriate for current platform.
    """
    @classmethod
    def format_disk(cls, disk):
        """ Format a disk.

        Args:
            disk (str): ``(ex: '/dev/sda1', '/home/out.img')``
                file representing a disk partition
        """
        cmds = ['mkfs', '-t', cls.filesystem(), disk]
        subprocess.check_call(cmds, universal_newlines=True)

    @staticmethod
    def filesystem():
        """ Obtain filesystem for current platform.
        """
        filesystems = {
            'FreeBSD': 'ufs',
            'Linux': 'ext4',
        }
        platform_ = platform.system()
        if platform_ in filesystems:
            return filesystems[platform_]
        raise NotImplementedError('platform not implemented: {}'.format(platform_))


class Disk:
    """ A disk with a capacity of 5M.
    """
    def __init__(self, path):
        self._path = path

    @property
    def path(self):
        return self._path

    def create(self):
        """ Create a file to represent a disk partition.
        """
        cmds = ['dd', 'if=/dev/zero', 'of={}'.format(self.path), 'bs=1M', 'count=5']
        subprocess.check_call(cmds, universal_newlines=True)

    def format(self):
        Filesystem.format_disk(self.path)

    def mount(self, location):
        cmds = ['sudo', 'mount', '-t', Filesystem.filesystem(), self.path, location]
        subprocess.check_call(cmds, universal_newlines=True)
        cmds = ['sudo', 'chmod', '-R', '777', location]
        subprocess.check_call(cmds, universal_newlines=True)

    def unmount(self):
        cmds = ['sudo', 'umount', '-f', self.path]
        subprocess.check_call(cmds, universal_newlines=True)

    def delete(self):
        os.remove(self.path)


class File:
    """ A 1M file.
    """ 
    def __init__(self, path):
        self._path = path

    @property
    def path(self):
        return self._path

    def __str__(self):
        return self._path

    def create(self):
        cmds = ['dd', 'if=/dev/zero', 'of={}'.format(self.path), 'bs=1M', 'count=1']
        subprocess.check_call(cmds, universal_newlines=True)


if __name__ == '__main__':
    test = InteractiveTestWithDiskRequest()
    test.perform()

