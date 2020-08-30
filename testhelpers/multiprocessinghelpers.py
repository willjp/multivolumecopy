import contextlib
import functools
import mock


class MockPool(mock.Mock):
    """ Mock object, runs apply within the caller process
    instead worker processes. (not async and obeys mocks).
    """
    def apply(self, func, args=None, kwargs=None):
        args = args or tuple()
        kwargs = kwargs or {}
        return functools.partial(func, *args, **kwargs)()

    def __enter__(self, *args, **kwags):
        return self

    def __exit__(self, *args, **kwargs):
        pass


@contextlib.contextmanager
def mock_pool():
    """ contextmanager that mocks multiprocessing.Pool with `MockPool`.
    """
    pool = MockPool()
    with mock.patch('multiprocessing.Pool', return_value=pool) as m_pool:
        yield m_pool


