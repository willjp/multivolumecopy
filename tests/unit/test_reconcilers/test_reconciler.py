from multivolumecopy import copyoptions, copyfile
from multivolumecopy.reconcilers import reconciler
from testhelpers import filesystemhelpers
import mock


class DummyReconciler(reconciler.Reconciler):
    def calculate(self, copyfiles, copied_indexes):
        return {'/dst/a/1.txt', '/dst/0.txt'}


class TestReconciler:
    def setup(self):
        self.copyfiles = tuple([
            copyfile.CopyFile(src='/src/0.txt', dst='/dst/0.txt',
                              relpath='0.txt', bytes=1024, index=0),
            copyfile.CopyFile(src='/src/a/1.txt', dst='/dst/a/1.txt',
                              relpath='a/1.txt', bytes=1024, index=1),
            copyfile.CopyFile(src='/src/a/2.txt', dst='/dst/a/2.txt',
                              relpath='a/2.txt', bytes=1024, index=2),
        ])
        self.resolver = mock.Mock()

        self.options = copyoptions.CopyOptions()
        self.options.output = '/dst'

    @mock.patch('os.rmdir')
    @mock.patch('os.remove')
    def test_reconcile_deletes_files(self, m_remove, m_rmdir):
        """ Independent of implementation, calculate() returned files are removed.
        """
        reconciler_ = DummyReconciler(self.resolver, self.options)
        reconciler_.reconcile(self.copyfiles, copied_indexes=[])
        expected_calls = [mock.call('/dst/a/1.txt'), mock.call('/dst/0.txt')]
        m_remove.assert_has_calls(expected_calls, any_order=True)

    @mock.patch('os.rmdir')
    @mock.patch('os.remove')
    def test_reconcile_deletes_leftover_empty_dirs(self, m_remove, m_rmdir):
        reconciler_ = DummyReconciler(self.resolver, self.options)
        walk_paths = {'/dst': [('/dst', ['a'], []),
                               ('/dst/a', [], []),
                               ('/dst/a/b', [], [])]}

        with filesystemhelpers.mock_walk(walk_paths):
            reconciler_.reconcile(self.copyfiles, copied_indexes=[])

        expected_calls = [mock.call('/dst/a/b'), mock.call('/dst/a')]
        m_rmdir.assert_has_calls(expected_calls, any_order=True)
