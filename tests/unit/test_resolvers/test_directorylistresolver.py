from multivolumecopy.resolvers import directorylistresolver
from multivolumecopy import copyoptions
import pytest


@pytest.fixture
def options():
    options = copyoptions.CopyOptions()
    options.output = '/dst'
    return options


class TestDirectoryListResolver:
    def test_sets_relpath(self):
        assert False

    def test_sets_dst(self):
        assert False

    def test_sets_src(self):
        assert False

    def test_sets_bytes(self):
        assert False

    def test_sets_index(self):
        assert False

    def test_result_sorted_alphabetical_by_src(self):
        assert False

    def test_merges_multiple_sources(self):
        assert False
