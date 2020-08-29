from multivolumecopy import copyoptions
from multivolumecopy.progress import lineformatter
import pytest


@pytest.fixture
def valid_filedata():
    return {"src": "/src/a.txt", "dst": "/dst/a.txt", "relpath": "a.txt", "bytes": 1000, "index": 1}


class TestLineFormatter:
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
        formatter = lineformatter.LineFormatter(fmt=fmt)
        formatter.format(index=0, lastindex_total=1, error_indexes=[], filedata=valid_filedata)

