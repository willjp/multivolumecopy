from multivolumecopy import copyoptions
import mock
import pytest


class TestCopyOptions:
    @pytest.mark.parametrize('provided_value, saved_value', [
        ('1M', 1000000),
        (1024, 1024),
        (None, 0)])
    def test_device_padding_converted_to_bytes(self, provided_value, saved_value):
        options = copyoptions.CopyOptions()
        options.device_padding = provided_value
        assert options.device_padding == saved_value

    def test_num_workers_defaults_to_one_if_only_one_cpu(self):
        with mock.patch('multiprocessing.cpu_count', return_value=1):
            options = copyoptions.CopyOptions()
            assert options.num_workers == 1

    def test_num_workers_defaults_to_avail_cpus_minus_one_if_multi_cpu(self):
        with mock.patch('multiprocessing.cpu_count', return_value=4):
            options = copyoptions.CopyOptions()
            assert options.num_workers == 2

    @pytest.mark.skip(reason='not implemented yet')
    def test_valid(self):
        assert False
