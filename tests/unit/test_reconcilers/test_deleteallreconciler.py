from multivolumecopy.reconcilers import deleteallreconciler
from multivolumecopy import copyoptions, copyfile
from testhelpers import filesystemhelpers
import mock


class TestDeleteAllReconciler:
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

    @mock.patch('multivolumecopy.filesystem.volume_free', return_value=8192)
    def test_calculate_indicates_all_files_should_be_deleted(self, m_free):
        """ Deletes all files, no matter what has been backed up, or is going to be backed up.
        """
        # files are unrelated to backup
        walk_paths = {'/dst': [('/dst', ['/a'], ['x0.txt']),
                               ('/dst/a', [], ['x1.txt'])]}
        copied_indexes = []
        reconciler = deleteallreconciler.DeleteAllReconciler(self.resolver, self.options)
        with filesystemhelpers.mock_walk(walk_paths):
            filepaths = reconciler.calculate(self.copyfiles, copied_indexes)
        assert filepaths == {'/dst/a/x1.txt', '/dst/x0.txt'}


