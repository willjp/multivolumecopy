#!/usr/bin/env python
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from multivolumecopy import filesystem
import mock
import pytest


ns = filesystem.__name__


class Test_size_to_bytes(object):
    @pytest.mark.parametrize(
        'size, size_in_bytes',
        [
            ('100T',   100000000000000),
            ('100TB',  100000000000000),
            ('100G',   100000000000),
            ('100GB',  100000000000),
            ('100M',   100000000),
            ('100MB',  100000000),
            ('100K',   100000),
            ('100KB',  100000),
            ('1B',     1),
            (1,        1),
        ]
    )
    def test(self, size, size_in_bytes):
        result = filesystem.size_to_bytes(size)
        assert result == size_in_bytes


class Test_backup_bytes(object):
    def test(self):
        def walk_results(srcpath, *args, **kwargs):
            for result in (
                ('/dst', ['a', 'b'], ['file.txt']),
                ('/dst/a', [], ['file.txt']),
                ('/dst/b', [], ['file.txt']),
            ):
                yield result

        with mock.patch('{}.os.walk'.format(ns), side_effect=walk_results):
            with mock.patch('{}.os.path.getsize'.format(ns), return_value=1000):
                result = filesystem.backup_bytes('/dst')
                # adds size of 2x directories, and 3x files (all whose value
                # here is 100) bytes)
                assert result == 5000


class Test_get_mount(object):
    def test(self):
        def ismount(path):
            if path == '/mnt/movies':
                return True
            return False

        with mock.patch('{}.os.path.ismount'.format(ns), side_effect=ismount):
            mount = filesystem.get_mount('/mnt/movies/amelie/amelie.mkv')
            assert mount == '/mnt/movies'


class Test_files_different(object):
    def test_different_mtime(self):
        result = self.files_different(
            mtime=True, size=False, checksum=False,
            mtime_a=111.1, mtime_b=222.2,
        )
        assert result is True

    def test_different_size(self):
        result = self.files_different(
            mtime=False, size=True, checksum=False,
            size_a=1024.0, size_b=2048.0,
        )
        assert result is False

    def test_same_mtime(self):
        result = self.files_different(
            mtime=True, size=False, checksum=False,
            mtime_a=111.1, mtime_b=111.1,
        )
        assert result is False

    def test_same_size(self):
        result = self.files_different(
            mtime=False, size=True, checksum=False,
            size_a=1024.0, size_b=1024.0,
        )
        assert result is True

    def files_different(
        self,
        mtime=False,
        size=False,
        checksum=False,
        mtime_a=None,
        mtime_b=None,
        size_a=None,
        size_b=None,
        checksum_a=None,
        checksum_b=None
    ):
        def getmtime(path):
            if path == '/a.txt':
                return mtime_a
            elif path == '/b.txt':
                return mtime_b
            raise RuntimeError('bad test data')

        def getsize(path):
            if path == '/a.txt':
                return size_a
            elif path == '/b.txt':
                return size_b
            raise RuntimeError('bad test data')

        def getchecksum(path):
            if path == '/a.txt':
                return checksum_a
            elif path == '/b.txt':
                return checksum_b
            raise RuntimeError('bad test data')

        with mock.patch('{}.os.path.getmtime'.format(ns), side_effect=getmtime):
            with mock.patch('{}.os.path.getsize'.format(ns), side_effect=getsize):
                result = filesystem.files_different('/a.txt', '/b.txt', mtime=mtime, size=size, checksum=checksum)
                return result


class Test_copyfile(object):
    def test_dst_not_exist(self):
        result = self.copyfile(dst_exists=False)
        assert result is True

    def test_dst_is_different(self):
        result = self.copyfile(dst_exists=True, dst_different=True)
        assert result is True

    def test_dst_is_same(self):
        result = self.copyfile(dst_exists=True, dst_different=False)
        assert result is False

    def copyfile(self, dst_exists=False, dst_different=False):
        with mock.patch('{}.shutil'.format(ns)):
            with mock.patch('{}.os'.format(ns)) as mock_os:
                with mock.patch('{}.files_different'.format(ns), return_value=dst_different):
                    mock_os.path.isfile = mock.Mock(return_value=dst_exists)
                    return filesystem.copyfile('/src/file.txt', '/dst/file.txt')


class Test_copyfilestat(object):
    def test_file2file(self):
        calls = self.copyfilestat('/src/file.txt', '/dst/file.txt')
        assert calls == [mock.call.copystat('/src/file.txt', '/dst/file.txt')]

    def test_with_nested_dirs(self):
        calls = self.copyfilestat('/src/path/to/file.txt', '/dst/path/to/file.txt')
        assert calls == [
            mock.call.copystat('/src/path',             '/dst/path'),
            mock.call.copystat('/src/path/to',          '/dst/path/to'),
            mock.call.copystat('/src/path/to/file.txt', '/dst/path/to/file.txt'),
        ]

    def copyfilestat(self, src, dst):
        with mock.patch('{}.shutil'.format(ns)) as mock_shutil:
            filesystem.copyfilestat(src, dst)
            return mock_shutil.mock_calls


class Test_common_relpath(object):
    def test_file2file(self):
        result = filesystem.common_relpath('/src/file.txt', '/dst/file.txt')
        assert result == 'file.txt'

    def test_different_dst_depth(self):
        result = filesystem.common_relpath('/src/file.txt', '/dst/path/file.txt')
        assert result == 'file.txt'

    def test_different_src_depth(self):
        result = filesystem.common_relpath('/src/path/file.txt', '/dst/file.txt')
        assert result == 'file.txt'

    def test_different_root_depths(self):
        result = filesystem.common_relpath('/src/some/path/file.txt', '/dst/some/path/to/file.txt')
        assert result == 'file.txt'

    def test_relpath_has_dirs(self):
        result = filesystem.common_relpath('/src/path/to/file.txt', '/dst/path/to/file.txt')
        assert result == 'path/to/file.txt'
