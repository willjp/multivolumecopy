from multivolumecopy import copyoptions
from multivolumecopy.progress import simpleprogressformatter
import pytest


@pytest.fixture
def valid_filedata():
    return {"src": "/src/a.txt", "dst": "/dst/a.txt", "relpath": "a.txt", "bytes": 1000, "index": 1}


class TestSimpleProgressFormatter:
    @pytest.mark.parametrize('key', [
        'total_copied',
        'total_files',
        'total_percent',
        'total_progressbar',
        'last_file_full',
        'last_file_abbrev',
        'num_errors',
    ])
    def test_supported_types(self, key, valid_filedata):
        # verify it runs without exception.
        fmt = '{' + key + '}'
        formatter = simpleprogressformatter.SimpleProgressFormatter(fmt=fmt)
        formatter.format(index=0, lastindex_total=1, filedata=valid_filedata)

    def test_percentage_when_total_is_0(self, valid_filedata):
        fmt = '{total_percent}'
        formatter = simpleprogressformatter.SimpleProgressFormatter(fmt=fmt)
        result = formatter.format(index=0, lastindex_total=0, filedata=valid_filedata)
        assert result == '\r0.0'

    def test_percentage_when_total_is_not_0(self, valid_filedata):
        fmt = '{total_percent}'
        formatter = simpleprogressformatter.SimpleProgressFormatter(fmt=fmt)
        result = formatter.format(index=2, lastindex_total=4, filedata=valid_filedata)
        assert result == '\r50.0'
