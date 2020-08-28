from multivolumecopy import filesystem
import multiprocessing
import numbers
import os


class CopyOptions(object):
    """ Stores Configuration of this copyjob.
    """
    def __init__(self):
        # =============
        # with defaults
        # =============

        # begin copying from this jobfile index
        # (used if you experienced fails while on at least the second volume)
        self.start_index = 0

        # leave this much room free on the device (bytes)
        self.device_padding = None

        # display progressbar while copying
        self.show_progressbar = False

        # file that jobfiles are recorded to [TODO]
        self.jobfile = os.path.abspath('./.mvcopy-jobdata.json')

        # file that current index is recorded to [TODO]
        self.indexfile = os.path.abspath('./.mvcopy-index')

        # maximum copy operations a worker can live through.
        # (afterwards it's process is restarted to free up memory)
        # (this adds up quickly, watch your process in top/taskmanager)
        self.max_worker_tasks = 5

        # Desired number of worker processes to execute copies
        # more workers == more ram. Conservative is better.
        self.num_workers = (multiprocessing.cpu_count() - 1) or 1

        # ================
        # without defaults
        # ================
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
        elif not isinstance(value, numbers.Number):
            self._device_padding = filesystem.size_to_bytes(value)
        else:
            self._device_padding = int(value)


