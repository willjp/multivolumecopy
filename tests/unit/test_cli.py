# builtin
from __future__ import unicode_literals
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
# package
# external
import mock
import pytest
# internal
from multivolumecopy import cli


ns = cli.__name__


@pytest.fixture
def mock_args():
    _mock_args = mock.Mock()
    _mock_args.srcpaths = None
    _mock_args.output = None
    _mock_args.padding = None

    return _mock_args


class Test_CommandlineInterface(object):
    def test_no_device_padding(self, mock_args):
        mock_args.srcpaths = ['/src']
        mock_args.output = '/dst'
        result = self.cli(mock_args)

        assert result == [mock.call(srcpaths=['/src'], output='/dst', device_padding=None)]

    def test_with_device_padding(self, mock_args):
        mock_args.srcpaths = ['/src']
        mock_args.output = '/dst'
        mock_args.padding = '5M'
        result = self.cli(mock_args)

        assert result == [mock.call(srcpaths=['/src'], output='/dst', device_padding='5M')]

    def cli(self, args):
        if not isinstance(args, mock.Mock):
            raise TypeError()

        cli_ = cli.CommandlineInterface()
        cli_.parser.parse_args = args

        with mock.patch('{}.sys'.format(ns)):
            with mock.patch.object(cli_.parser, 'parse_args', return_value=args):
                with mock.patch('{}.mvcopy.mvcopy'.format(ns)) as mock_mvcopy:
                    cli_.parse_args()
                    return mock_mvcopy.mock_calls
