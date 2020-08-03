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
    """ default cli-arg values
    """
    _mock_args = mock.Mock()
    _mock_args.srcpaths = None
    _mock_args.jobfile = None
    _mock_args.output = None
    _mock_args.device_padding = None
    _mock_args.no_progress = False

    return _mock_args


class Test_CommandlineInterface(object):
    def test_no_device_padding(self, mock_args):
        mock_args.srcpaths = ['/src']
        mock_args.output = '/dst'
        result = self.cli(mock_args)
        expects = mock.call(['/src'], output='/dst', device_padding=None, no_progressbar=False)

        assert result == [expects]

    def test_with_device_padding(self, mock_args):
        mock_args.srcpaths = ['/src']
        mock_args.output = '/dst'
        mock_args.device_padding = '5M'
        result = self.cli(mock_args)
        expects = mock.call(['/src'], output='/dst', device_padding='5M', no_progressbar=False)

        assert result == [expects]

    def cli(self, args):
        if not isinstance(args, mock.Mock):
            raise TypeError()

        cli_ = cli.CommandlineInterface()
        cli_.parser.parse_args = args

        with mock.patch('{}.sys'.format(ns)):
            with mock.patch.object(cli_.parser, 'parse_args', return_value=args):
                with mock.patch('{}.mvcopy.mvcopy_srcpaths'.format(ns)) as mock_mvcopy:
                    cli_.parse_args()
                    return mock_mvcopy.mock_calls
