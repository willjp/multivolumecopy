from multivolumecopy.resolvers import jobfileresolver
from multivolumecopy import copyoptions
from testhelpers import multiprocessinghelpers
import mock


FS = jobfileresolver.__name__


class TestJobFileResolver:
    def setup(self):
        self.options = copyoptions.CopyOptions()
        self.options.dst = '/dst'

    def test_loads_json(self):
        resolver = jobfileresolver.JobFileResolver("/var/tmp/.mvcopy-jobfile.json", self.options)
        read_mock = mock.mock_open(read_data='[["/src/a/b.txt", "/dst/a/b.txt", "a/b.txt", 1024, 0]]')
        with mock.patch('{}.open'.format(FS), read_mock):
            with multiprocessinghelpers.mock_pool():
                copyfiles = resolver.get_copyfiles()
                # important for mem usage
                assert isinstance(copyfiles, tuple)
                copyfile = copyfiles[0]
                assert copyfile.src == "/src/a/b.txt"
                assert copyfile.dst == "/dst/a/b.txt"
                assert copyfile.relpath == "a/b.txt"
                assert copyfile.bytes == 1024
                assert copyfile.index == 0


