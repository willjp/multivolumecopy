import contextlib
import mock
import os


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

