from multivolumecopy.reconcilers import keepfilesreconciler
from multivolumecopy.resolvers import resolver
from multivolumecopy import copyoptions
import mock
import os
import contextlib


NS = keepfilesreconciler.__file__


@contextlib.contextmanager
def mock_walk(walk_paths=None):
    walk_paths = walk_paths or {}
    def walk_results(srcpath, *args, **kwargs):
        if srcpath not in walk_paths:
            return os.walk(srcpath, *args, **kwargs)
        for copyfile in walk_paths[srcpath]:
            yield copyfile

    with mock.patch('os.walk', side_effect=walk_results) as mock_walk_:
        yield mock_walk_


@contextlib.contextmanager
def mock_isfile(mocked_paths):
    def isfile_results(filepath):
        if filepath in mocked_paths:
            return mocked_paths[filepath]
        return os.path.isfile(filepath)

    with mock.patch('os.path.isfile', side_effect=isfile_results) as mock_isfile_:
        yield mock_isfile_


class TestKeepFilesReconciler:
    def setup(self):
        self.copyfiles = tuple([
            resolver.CopyFile(src='/src/0.txt', dst='/dst/0.txt',
                              relpath='0.txt', bytes=1024, index=0),
            resolver.CopyFile(src='/src/a/1.txt', dst='/dst/a/1.txt',
                              relpath='a/1.txt', bytes=1024, index=1),
            resolver.CopyFile(src='/src/a/2.txt', dst='/dst/a/2.txt',
                              relpath='a/2.txt', bytes=1024, index=2),
        ])
        self.resolver = mock.Mock()

        self.options = copyoptions.CopyOptions()
        self.options.output = '/dst'

    @mock.patch('multivolumecopy.reconcilers.keepfilesreconciler.KeepFilesReconciler.calculate', 
                return_value=['/dst/a/1.txt', '/dst/0.txt'])
    @mock.patch('os.remove')
    def test_reconcile_deletes_files(self, m_remove, m_calculate):
        """ Independent of implementation, calculate() returned files are removed.
        """
        reconciler = keepfilesreconciler.KeepFilesReconciler(self.resolver, self.options)
        reconciler.reconcile(self.copyfiles, copied_indexes=[])
        m_remove.assert_has_calls([mock.call('/dst/a/1.txt'), mock.call('/dst/0.txt')])

    @mock.patch('multivolumecopy.filesystem.volume_free', return_value=8192)
    def test_calculate_indicates_removal_of_unrelated_files(self, m_free):
        """ Indicate removal of files that are not a part of the backup.
        """
        # files are unrelated to backup
        walk_paths = {'/dst': [('/dst', ['/a'], ['x0.txt']),
                               ('/dst/a', [], ['x1.txt'])]}
        copied_indexes = []
        reconciler = keepfilesreconciler.KeepFilesReconciler(self.resolver, self.options)
        with mock_walk(walk_paths):
            filepaths = reconciler.calculate(self.copyfiles, copied_indexes)
        assert filepaths == {'/dst/a/x1.txt', '/dst/x0.txt'}

    @mock.patch('multivolumecopy.filesystem.volume_free', return_value=8192)
    def test_calculate_indicates_removal_of_already_copied_files(self, m_free):
        """ Indicate removal of files that have been already copied to another device.

        Notes:
            The reconciler runs first wtih device-index, second with
            the last successfully copied index once a device is full.

            `copied_indexes` in both cases indicate files that do not belong on this device,
            and they should be removed.
        """
        # files belong to backup, but have been copied to another device
        # (indicated by copied_indexes)
        walk_paths = {'/dst': [('/dst', ['a'], ['0.txt']),
                               ('/dst/a', [], ['2.txt'])]}
        copied_indexes = [0, 2]
        reconciler = keepfilesreconciler.KeepFilesReconciler(self.resolver, self.options)
        with mock_walk(walk_paths):
            filepaths = reconciler.calculate(self.copyfiles, copied_indexes)
        assert filepaths == {'/dst/0.txt', '/dst/a/2.txt'}

    @mock.patch('multivolumecopy.filesystem.volume_free', return_value=1200)
    def test_calculate_indicates_removal_of_files_device_will_not_have_room_for(self, m_free):
        """ Indicate removal of files that won't fit on this device.
        """
        # volume has enough room for 1x 1024b file.
        isfile_results = {'/dst/0.txt': True,
                          '/dst/a/1.txt': True,
                          '/dst/a/2.txt': True}
        copied_indexes = []
        reconciler = keepfilesreconciler.KeepFilesReconciler(self.resolver, self.options)
        with mock_isfile(isfile_results):
            filepaths = reconciler.calculate(self.copyfiles, copied_indexes)
        assert filepaths == {'/dst/a/1.txt', '/dst/a/2.txt'}
