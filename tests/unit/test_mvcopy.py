#!/usr/bin/env python
# builtin
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
import os
# package
# external
import mock
import pytest
# internal
from multivolumecopy import mvcopy, filesystem


ns = mvcopy.__name__
sample_copyfiles = [
    {'src': '/src/a.txt', 'dst': '/dst/a.txt', 'relpath': 'a.txt', 'bytes': 1000},
    {'src': '/src/b.txt', 'dst': '/dst/b.txt', 'relpath': 'b.txt', 'bytes': 1000},
    {'src': '/src/c.txt', 'dst': '/dst/c.txt', 'relpath': 'c.txt', 'bytes': 1000},
    {'src': '/src/d.txt', 'dst': '/dst/d.txt', 'relpath': 'd.txt', 'bytes': 1000},
    {'src': '/src/e.txt', 'dst': '/dst/e.txt', 'relpath': 'e.txt', 'bytes': 1000},
]


class Test_mvcopy(object):
    def test_no_rollover_reqd(self):
        result = self.mvcopy(
            lastindexes=[1],
            copyfiles=[
                {'src': '/tmp/src/a.txt', 'dst': '/tmp/dst/a.txt', 'relpath': 'a.txt', 'bytes': 1024},
                {'src': '/tmp/src/b.txt', 'dst': '/tmp/dst/b.txt', 'relpath': 'b.txt', 'bytes': 1024},
            ]
        )
        assert result['prompt_diskfull_calls'] == []
        assert result['copyfile_calls'] == [
            mock.call(src='/tmp/src/a.txt', dst='/tmp/dst/a.txt'),
            mock.call(src='/tmp/src/b.txt', dst='/tmp/dst/b.txt'),
        ]

    def test_disk_full_rollover(self):
        result = self.mvcopy(
            lastindexes=[2, 4],
            copyfiles=sample_copyfiles,
        )
        assert result['prompt_diskfull_calls'] == [mock.call('/dst')]
        assert result['copyfile_calls'] == [
            mock.call(src='/src/a.txt', dst='/dst/a.txt'),
            mock.call(src='/src/b.txt', dst='/dst/b.txt'),
            mock.call(src='/src/c.txt', dst='/dst/c.txt'),
            mock.call(src='/src/d.txt', dst='/dst/d.txt'),
            mock.call(src='/src/e.txt', dst='/dst/e.txt'),
        ]

    def mvcopy(self, lastindexes, copyfiles):
        """ Runs mvcopy() mocked, returns items to test.

        Args:
            lastindexes (list): ``(ex: [2], [0,5])``
                a list of copyfile indexes. Each represents one volume
                being filled.

            copyfiles (list):
                A list of copyfile dictionaries representing all files to be copied
                during this `mvcopy` operation.

                .. code-block:: python

                    [
                        {'src': '/tmp/src/a.txt', 'dst': '/tmp/dst/a.txt', 'relpath': 'a.txt', 'bytes': 1024},
                        {'src': '/tmp/src/b.txt', 'dst': '/tmp/dst/b.txt', 'relpath': 'b.txt', 'bytes': 1024},
                    ]

        Returns:
        """
        if lastindexes[-1] != len(copyfiles) - 1:
            raise RuntimeError('bad test data')

        with mock.patch('{}._prompt_diskfull'.format(ns)) as mock_diskfull:
            with mock.patch('{}.filesystem'.format(ns)) as mock_filesystem:
                with mock.patch('{}._get_volume_lastindex'.format(ns), side_effect=lastindexes):
                    with mock.patch('{}.list_copyfiles'.format(ns), return_value=copyfiles):
                        mvcopy.mvcopy(
                            srcpaths=['/src'],
                            output='/dst',
                        )
        return dict(
            prompt_diskfull_calls=mock_diskfull.mock_calls,
            copyfile_calls=mock_filesystem.copyfile.mock_calls,
        )


class Test_list_copyfiles(object):
    def test_flat_files(self):
        result = self.list_copyfiles(
            srcpath_walk={
                '/tmp/src': [
                    ('/tmp/src', [], ['a.txt', 'b.txt']),
                ]
            },
            dstdir='/tmp/dst',
        )
        assert result == [
            {'src': '/tmp/src/a.txt', 'dst': '/tmp/dst/a.txt', 'relpath': 'a.txt', 'bytes': 1024},
            {'src': '/tmp/src/b.txt', 'dst': '/tmp/dst/b.txt', 'relpath': 'b.txt', 'bytes': 1024},
        ]

    def test_subdirectories(self):
        result = self.list_copyfiles(
            srcpath_walk={
                '/tmp/src': [
                    ('/tmp/src', [], ['A/a.txt', 'A/B/b.txt']),
                ]
            },
            dstdir='/tmp/dst',
        )
        assert result == [
            {'src': '/tmp/src/A/a.txt', 'dst': '/tmp/dst/A/a.txt', 'relpath': 'A/a.txt', 'bytes': 1024},
            {'src': '/tmp/src/A/B/b.txt', 'dst': '/tmp/dst/A/B/b.txt', 'relpath': 'A/B/b.txt', 'bytes': 1024},
        ]

    def test_relative_srcpath(self):
        result = self.list_copyfiles(
            srcpath_walk={
                '/var/tmp/src': [
                    ('src', [], ['a.txt']),
                ]
            },
            dstdir='/tmp/dst',
        )
        assert result == [
            {'src': '/var/tmp/src/a.txt', 'dst': '/tmp/dst/a.txt', 'relpath': 'a.txt', 'bytes': 1024},
        ]

    def test_relative_dstpath(self):
        result = self.list_copyfiles(
            srcpath_walk={
                '/var/tmp/src': [
                    ('src', [], ['a.txt']),
                ]
            },
            dstdir='dst',
        )
        assert result == [
            {'src': '/var/tmp/src/a.txt', 'dst': '/var/tmp/dst/a.txt', 'relpath': 'a.txt', 'bytes': 1024},
        ]

    def list_copyfiles(self, srcpath_walk, dstdir):
        """ Runs the test.

        Args:
            srcpath_walk (dict): dictionary of src-dirs, and a list of files they contain.
            dstdir (str):        where file is copied to.
        """
        def walk_results(srcpath, *args, **kwargs):
            for copyfile in srcpath_walk[srcpath]:
                yield copyfile

        with mock.patch('{}.os.path.getsize'.format(ns), return_value=1024):
            with mock.patch('{}.os.walk'.format(ns), side_effect=walk_results):
                with mock.patch.object(os, 'getcwd', return_value='/var/tmp'):

                    copyfiles = mvcopy.list_copyfiles(list(srcpath_walk.keys()), dstdir)
                    return copyfiles


class Test__get_volume_lastindex(object):
    @pytest.mark.parametrize(
        'devpadding, capacity, index, expected', [
            (50,     2000,     0,     1),
            (999,    2000,     0,     1),
            (50,     3000,     0,     2),
        ]
    )
    def test(self, devpadding, capacity, index, expected):
        """

        Args:
            devpadding (int):
                Size in bytes to leave free on a drive before requesting backup-media.

            capacity (int):
                room left on device.

            index (int):
                index of the current copyfile. (the first file to be copied on this volume).
        """
        with mock.patch('{}.avail_bytes_for_backup'.format(filesystem.__name__), return_value=capacity):
            lastindex = mvcopy._get_volume_lastindex(
                index=index,
                output='/dst',
                copyfiles=sample_copyfiles,
                device_padding=devpadding,
            )
            assert lastindex == expected


class Test__volume_delete_extraneous(object):
    def test_no_deleted_files_match_files_to_be_copied(self):
        delete_calls = self.volume_delete_extraneous(
            firstindex=0,
            lastindex=2,
            copyfiles=sample_copyfiles,
            current_outputfiles=sample_copyfiles,
        )
        expected_deletes = [d['dst'] for d in sample_copyfiles[3:]]
        assert delete_calls == [mock.call(fp) for fp in expected_deletes]

    def test_empty_outdir(self):
        delete_calls = self.volume_delete_extraneous(
            firstindex=0,
            lastindex=2,
            copyfiles=sample_copyfiles,
            current_outputfiles=[],
        )
        expected_deletes = []
        assert delete_calls == [mock.call(fp) for fp in expected_deletes]

    def test_copyfiles_matches_outfiles(self):
        delete_calls = self.volume_delete_extraneous(
            firstindex=0,
            lastindex=len(sample_copyfiles) - 1,
            copyfiles=sample_copyfiles,
            current_outputfiles=sample_copyfiles,
        )
        expected_deletes = []
        assert delete_calls == [mock.call(fp) for fp in expected_deletes]

    def test_mixed_overlapping_non_overlapping(self):
        delete_calls = self.volume_delete_extraneous(
            firstindex=0,
            lastindex=2,
            copyfiles=sample_copyfiles,
            current_outputfiles=[
                {'src': '/src/a.txt',         'dst': '/dst/a.txt',         'relpath': 'a.txt',         'bytes': 1000},
                {'src': '/src/deleteme.txt',  'dst': '/dst/deleteme.txt',  'relpath': 'deleteme.txt',  'bytes': 1000},
            ],
        )
        expected_deletes = ['/dst/deleteme.txt']
        assert delete_calls == [mock.call(fp) for fp in expected_deletes]

    def volume_delete_extraneous(self, firstindex, lastindex, copyfiles, current_outputfiles):
        def os_walk(*args, **kwargs):
            # root, dirnames, filenames
            yield ('/dst', [], [os.path.basename(d['dst']) for d in current_outputfiles])

        with mock.patch('{}.os.remove'.format(ns)) as mock_remove:
            with mock.patch('{}.os.walk'.format(ns), side_effect=os_walk):
                lastindex = mvcopy._volume_delete_extraneous(
                    index=firstindex,
                    lastindex=lastindex,
                    copyfiles=copyfiles,
                    output='/dst',
                )
                return mock_remove.mock_calls
