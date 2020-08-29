# builtin
from __future__ import unicode_literals
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
import sys
import mock
import pytest
from multivolumecopy import cli


class Test_CommandlineInterface(object):
    def setup(self):
        self.cli = cli.CommandlineInterface()

    @mock.patch('multivolumecopy.copiers.multiprocesscopier.MultiProcessCopier')
    def test_parse_args_sets_output(self, m_copier):
        sys.argv = ['multivolumecopy', '/src', '-o', '/dst']
        self.cli.parse_args()
        assert self.cli.options.output == '/dst'

    @mock.patch('multivolumecopy.copiers.multiprocesscopier.MultiProcessCopier')
    def test_parse_args_sets_device_padding(self, m_copier):
        sys.argv = ['multivolumecopy', '--device-padding', '5M', '/src', '-o', '/dst']
        self.cli.parse_args()
        assert self.cli.options.device_padding == 5000000

    @mock.patch('multivolumecopy.copiers.multiprocesscopier.MultiProcessCopier')
    def test_parse_args_sets_show_progressbar(self, m_copier):
        sys.argv = ['multivolumecopy', '--hide-progress', '/src', '-o', '/dst']
        self.cli.parse_args()
        assert self.cli.options.show_progressbar == False

    @mock.patch('multivolumecopy.copiers.multiprocesscopier.MultiProcessCopier')
    def test_parse_args_sets_select_index(self, m_copier_cls):
        m_copier = mock.Mock()
        m_copier_cls.return_value = m_copier

        sys.argv = ['multivolumecopy', '--select-index', '10', '/src', '-o', '/dst']
        self.cli.parse_args()
        m_copier.start.assert_called_with(None, 10)

    @mock.patch('multivolumecopy.copiers.multiprocesscopier.MultiProcessCopier')
    def test_parse_args_sets_device_index(self, m_copier_cls):
        m_copier = mock.Mock()
        m_copier_cls.return_value = m_copier

        sys.argv = ['multivolumecopy', '--device-startindex', '10', '/src', '-o', '/dst']
        self.cli.parse_args()
        m_copier.start.assert_called_with(10, None)

    @mock.patch('multivolumecopy.resolvers.jobfileresolver.JobFileResolver')
    @mock.patch('multivolumecopy.copiers.multiprocesscopier.MultiProcessCopier')
    def test_parse_args_sets_jobfile(self, m_copier_cls, m_resolver_cls):
        sys.argv = ['multivolumecopy', '--jobfile', '/tmp/.mvcopy-jobfile.json', '/src', '-o', '/dst']
        self.cli.parse_args()
        m_resolver_cls.assert_called_with('/tmp/.mvcopy-jobfile.json', self.cli.options)


