import functools
import sys
import mock


def mock_input(return_value):
    def mock_input_decorator(method):
        if sys.version_info[0] < 3:
            patch_path = '__builtin__.raw_input'
        else:
            patch_path = 'builtins.input'

        @mock.patch(patch_path, return_value=return_value)
        @functools.wraps(method)
        def wrapper(message, m_input):
            return method(message, m_input)
        return wrapper

    return mock_input_decorator


