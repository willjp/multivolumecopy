import multiprocessing
import numbers
import os


class CopyOptions(object):
    """ Stores Configuration of this copyjob.
    """
    def __init__(self):
        # with defaults
        self.start_index = 0
        self.device_padding = None
        self.show_progressbar = False
        self.jobfile = os.path.abspath('./.mvcopy-jobdata.json')
        self.indexfile = os.path.abspath('./.mvcopy-index')
        #self.num_workers = multiprocessing.cpu_count()
        self.num_workers = 1

        # without defaults
        self.output = None

    def validate(self):
        """ Returns true if combination of options is valid. Sets :py:meth:`errors`
        """
        raise NotImplementedError()

    @property
    def device_padding(self):
        """ Number of bytes to leave free on the device following copy.
        """
        return self._device_padding

    @device_padding.setter
    def device_padding(self, value):
        """ Set device padding from string, or int of bytes.

        Args:
            value (str, int): ``(ex: '1M', 1024)``
                string with single letter size indicator.
                or integer number of bytes.
        """
        if value is None:
            self._device_padding = 0
        elif not isinstance(device_padding, numbers.Number):
            self._device_padding = filesystem.size_to_bytes(device_padding)
        else:
            self._device_padding = int(value)


