from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from multivolumecopy.progress import textprogressbar


class LineFormatter(object):
    """ Formats a line with progress info.
    """
    def __init__(self, fmt=None):
        """ Constructor.

        Args:
            fmt (str, optional): ``(ex:  'Total {total_copied}/{total_files} [{total_progressbar}]' )``
                Determines infomation that will appear on the statusline.
        """
        self.fmt = fmt or ('(Total: {total_copied}/{total_files} {total_percent}%)'
                           '(Errors: {num_errors}) '
                           '[{total_progressbar}]  {last_file_abbrev} ')

        # number of characters shown in filename preview
        self.max_file_chars = 50

        self._progressbar = textprogressbar.TextProgressBar()

    def _format_options(self, index, lastindex_total, error_indexes, last_filedata):
        """
        Args:
            index (int):
                Index of last completed file in list of files.

            lastindex_total (int):
                The total number of files in this copy operation
                (unrelated to last index that will fit on currently mounted device)

            error_indexes (list):
                list of indexes of files that were unable to be copied.

            last_filedata (dict):
                dictionary with info about the last file that was successfully copied.

                .. code-block:: python

                    {'

        """
        # last_file
        if last_filedata:
            last_srcfile = last_filedata.get('src', '')
        else:
            last_srcfile = ''

        fmt_data = {'total_copied': index,
                    'total_files': lastindex_total,
                    'total_percent': round(self._progressbar.percent, 2),
                    'total_progressbar': self._progressbar.format(),
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

