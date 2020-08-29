from multivolumecopy.prompts import commandlineprompt
from testhelpers import consolehelpers
import sys
import pytest
import mock


class TestCommandlinePrompt:
    def setup(self):
        self.prompt = commandlineprompt.CommandlinePrompt()

    @mock.patch('__builtin__.raw_input')
    @pytest.mark.skipif(sys.version_info[0] >= 3, reason='raw_input only exists < python3')
    def test_python2_uses_raw_input(self, m_raw_input):
        self.prompt.input('Press Enter to Continue')
        assert m_raw_input.called

    @mock.patch('builtins.input')
    @pytest.mark.skipif(sys.version_info[0] < 3, reason='input only reliably exists >= python3')
    def test_python3_uses_input(self, m_input):
        if sys.version_info[0] < 3:
            pytest.skip('python-3+ specific test')

        self.prompt.input('Press Enter to Continue')
        assert m_input.called

    @consolehelpers.mock_input(return_value=b'abc')
    def test_input_returns_native_string_from_bytes(self, m_input):
        result = self.prompt.input('Press Enter to Continue')
        assert result == 'abc'

    @consolehelpers.mock_input(return_value=b'abc'.decode('utf-8'))
    def test_input_returns_native_string_from_unicode(self, m_input):
        result = self.prompt.input('Press Enter to Continue')
        assert result == 'abc'

