from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from multivolumecopy.progress import progressformatter


class SimpleProgressFormatter(progressformatter.ProgressFormatter):
    def __init__(self, fmt=None):
        self.fmt = fmt or ('(Total: {total_copied}/{total_files} {total_percent}%)'
                           '(Errors: {num_errors}) '
                           '[{total_progressbar}]  {last_file_abbrev} ')
        self.max_file_chars = 50
        self.progress_chars = 25
        self.progress_multiplier = int(100 / self.progress_chars)

    def _format_options(self, index, lastindex_total, error_indexes, last_filedata):
        # total relative data
        if lastindex_total == 0:
            total_percent = 0.0
            total_completed_steps = 0
            total_remaining_steps = self.progress_chars
        else:
            total_percent = (index / lastindex_total) * 100
            total_completed_steps = int(total_percent / 4)
            total_remaining_steps = int(self.progress_chars - total_completed_steps)
        total_progressbar = '{}{}'.format(('#' * total_completed_steps), (' ' * total_remaining_steps))

        # last_file
        if last_filedata:
            last_srcfile = last_filedata.get('src', '')
        else:
            last_srcfile = ''

        fmt_data = {'total_copied': index,
                    'total_files': lastindex_total,
                    'total_percent': round(total_percent, 2),
                    'total_progressbar': total_progressbar,
                    'last_file_full': self._abbreviated_file(last_srcfile, self.max_file_chars),
                    'last_file_abbrev': self._abbreviated_file(last_srcfile, self.max_file_chars),
                    'num_errors': len(error_indexes)}
        return fmt_data

    def _abbreviated_file(self, filepath, max_chars):
        if len(filepath) < max_chars:
            return filepath
        adjuster = -1 * max_chars
        return '...' + filepath[adjuster:]

    def format(self, index, lastindex_total, error_indexes, filedata):
        """ Formats a progressbar based on `fmt` string.

        Args:
            index (int):
                number of files copied successfully.

            lastindex_total (int):
                total number of files to copy (regardless how many devices

            filedata (dict):
                Dictionary of filedata.

                .. code-block:: python

                    {"src": "/src/a.txt", "dst": "/dst/a.txt", "relpath": "a.txt", "bytes": 1000, "index": 1},

        """
        fmt = self._format_options(index, lastindex_total, error_indexes, filedata)
        msg = '\r' + self.fmt.format(**fmt)
        return msg

