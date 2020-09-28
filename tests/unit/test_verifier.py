from unittest import mock

from multivolumecopy import copyfile
from multivolumecopy import copyoptions
from multivolumecopy import verifier
from multivolumecopy.resolvers import resolver


class FakeResolver(resolver.Resolver):
    """ Fake Resolver object that returns copyfiles assigned to `self.copyfiles` .
    """
    def __init__(self, copyfiles, options):
        """
        Args:
            copyfiles (list):
                List of files to "copy" in this test

                .. code-block:: python
    
                    [
                        CopyFile(src='/src/a.txt', dst='/dst/a.txt', relpath='a.txt', bytes=1024, index=0),
                        CopyFile(src='/src/b.txt', dst='/dst/b.txt', relpath='b.txt', bytes=1024, index=1),
                        CopyFile(src='/src/c.txt', dst='/dst/c.txt', relpath='c.txt', bytes=1024, index=2),
                        ...
                    ]

        """
        super(FakeResolver, self).__init__(options)
        self.copyfiles = copyfiles

    def get_copyfiles(self, device_start_index=None, start_index=None):
        if device_start_index:
            return self.copyfiles[device_start_index:]
        return self.copyfiles


class TestVerifier:
    def setup(self):
        options = copyoptions.CopyOptions()
        options.output = '/dst'
        self.resolver = FakeResolver([], options)
        self.verifier = verifier.Verifier(self.resolver, options)

    @mock.patch('os.path')
    @mock.patch('multivolumecopy.verifier.filesystem')
    def test_verify_identifies_changed_files(self, m_filesystem, m_os_path):
        # mocks
        copyfiles = self.gen_copyfiles(['a.txt', 'b.txt', 'c.txt'])
        self.resolver.copyfiles = copyfiles

        m_filesystem.files_different\
            .side_effect = \
            lambda src, dst, **kwargs: dst.endswith(('a.txt', 'c.txt'))

        m_filesystem.volume_capacity\
            .return_value = 4096

        m_os_path.isfile\
            .return_value = True

        # test
        results = self.verifier.verify(0, 3)
        assert [copyfiles[i].dst for i in results.different_indexes] == ['/dst/a.txt', '/dst/c.txt']

    @mock.patch('os.path')
    @mock.patch('multivolumecopy.verifier.filesystem')
    def test_verify_identifies_missing_files(self, m_filesystem, m_os_path):
        # mocks
        copyfiles = self.gen_copyfiles(['a.txt', 'b.txt', 'c.txt'])
        self.resolver.copyfiles = copyfiles

        m_filesystem.files_different\
            .return_value = False  # only interested in missing files

        m_filesystem.volume_capacity\
            .return_value = 4096

        m_os_path.isfile\
            .side_effect = lambda x: x not in ('/dst/a.txt', '/dst/c.txt')

        # test
        results = self.verifier.verify(0, 3)
        assert [copyfiles[i].dst for i in results.different_indexes] == ['/dst/a.txt', '/dst/c.txt']

    @mock.patch('os.path')
    @mock.patch('multivolumecopy.verifier.filesystem')
    def test_verify_skips_already_present_files(self, m_filesystem, m_os_path):
        # mocks -- all files show as copied && not-changed
        copyfiles = self.gen_copyfiles(['a.txt', 'b.txt', 'c.txt'])
        self.resolver.copyfiles = copyfiles

        m_filesystem.files_different\
            .return_value = False

        m_filesystem.volume_capacity\
            .return_value = 4096

        m_os_path.isfile\
            .return_value = True

        # test
        results = self.verifier.verify(0, 3)
        assert results.different_indexes == []

    @mock.patch('os.path')
    @mock.patch('multivolumecopy.verifier.filesystem')
    def test_verify_copied_size_sums_file_sizes(self, m_filesystem, m_os_path):
        # mocks -- copy all 3x 1024 byte files
        copyfiles = self.gen_copyfiles(['a.txt', 'b.txt', 'c.txt'])
        self.resolver.copyfiles = copyfiles

        m_filesystem.files_different\
            .return_value = True

        m_filesystem.volume_capacity\
            .return_value = 4096

        m_os_path.isfile\
            .return_value = True

        # test
        results = self.verifier.verify(0, 3)
        assert results.copied_bytes == 3072

    @mock.patch('os.path')
    @mock.patch('multivolumecopy.verifier.filesystem')
    def test_verify_copied_size_excludes_missing_files(self, m_filesystem, m_os_path):
        # mocks -- 2/3 files missing. The copied file not included in `copied_bytes`
        copyfiles = self.gen_copyfiles(['a.txt', 'b.txt', 'c.txt'])
        self.resolver.copyfiles = copyfiles

        m_filesystem.files_different\
            .return_value = False

        m_filesystem.volume_capacity\
            .return_value = 4096

        m_os_path.isfile\
            .side_effect = lambda x: x != '/dst/a.txt'  # all files different except for /dst/a.txt

        # test
        results = self.verifier.verify(0, 3)
        assert results.copied_bytes == 2048

    @mock.patch('os.path')
    @mock.patch('multivolumecopy.verifier.filesystem')
    def test_verify_sets_backup_bytes(self, m_filesystem, m_os_path):
        # mocks -- we don't care about anything except the reported directory_size
        copyfiles = self.gen_copyfiles(['a.txt', 'b.txt', 'c.txt'])
        self.resolver.copyfiles = copyfiles

        m_filesystem.files_different\
            .return_value = True

        m_filesystem.volume_capacity\
            .return_value = 4096

        m_os_path.isfile\
            .return_value = True

        m_filesystem.directory_size\
            .side_effect = lambda x: 4096 if x == '/dst' else 1024

        results = self.verifier.verify(0, 3)
        assert results.backup_bytes == 4096

    def gen_copyfiles(self, filenames):
        copyfiles = []
        for i in range(0, len(filenames)):
            filename = filenames[i]
            copyfile_ = copyfile.CopyFile(src='/src/{}'.format(filename),
                                          dst='/dst/{}'.format(filename),
                                          relpath=filename,
                                          bytes=1024,
                                          index=i)
            copyfiles.append(copyfile_)
        return copyfiles


