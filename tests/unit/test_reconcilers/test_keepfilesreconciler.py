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

    with mock.patch('os.walk', side_effect=walk_results) as mock_walk:
        yield mock_walk


class TestKeepFilesReconciler:
    def setup(self):
        self.copyfiles = tuple([
            resolver.CopyFile(src='/src/0.txt', dst='/dst/0.txt',
                              relpath='0.txt', bytes=1025, index=0),
            resolver.CopyFile(src='/src/a/1.txt', dst='/dst/a/1.txt',
                              relpath='a/1.txt', bytes=1025, index=1),
            resolver.CopyFile(src='/src/a/2.txt', dst='/dst/a/2.txt',
                              relpath='a/2.txt', bytes=1025, index=2),
        ])
        self.resolver = mock.Mock()

        self.options = copyoptions.CopyOptions()
        self.options.dst = '/dst'

    @mock.patch('os.remove')
    def test_removes_unrelated_files(self, m_remove):
        walk_paths = {
            '/dst': [('/dst', ['/a'], ['x0.txt']),
                     ('/dst/a', [], ['x1.txt'])],
        }
        copied_indexes = []
        reconciler = keepfilesreconciler.KeepFilesReconciler(self.resolver, self.options)
        with mock_walk(walk_paths):
            reconciler.reconcile(self.copyfiles, copied_indexes)
        m_remove.assert_has_calls([mock.call('/dst/a/x1.txt'), mock.call('/dst/a/x0.txt')])

    @mock.patch('os.remove')
    def test_removes_already_copied_files(self, m_remove):
        """ device_index indicates the first index to be copied to the currently
        mounted backup device. Files related to earlier indexes should be removed
        (since they were already backed up on another device).
        """
        copied_indexes = [0, 2]
        reconciler = keepfilesreconciler.KeepFilesReconciler(self.resolver, self.options)
        with mock_walk({}):
            reconciler.reconcile(self.copyfiles, copied_indexes)
        m_remove.assert_has_calls([mock.call('/dst/0.txt'), mock.call('/dst/a/2.txt')])

    def test_removes_files_device_will_not_have_room_for(self):
        assert False


