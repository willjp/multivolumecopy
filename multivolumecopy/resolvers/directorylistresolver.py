from multivolumecopy.resolvers import resolver
import os
import multivolumecopy.copyfile


class DirectoryListResolver(resolver.Resolver):
    """ Determine files to copy by recursing through a list of directories.
    """
    def __init__(self, directories, options):
        """ Constructor.

        Args:
            directories (list): ``(ex: ['/mnt/movies', '/mnt/music', ...])``
                A list of directories that you'd like to backup.
        """
        super(DirectoryListResolver, self).__init__(options)
        self._directories = directories

    def get_copyfiles(self, device_start_index=None):
        srcpaths = sorted([os.path.expanduser(p) for p in self._directories])
        copyfiles = self._list_copyfiles(srcpaths)

        # affects reconciliation and files to be copied.
        # determines when we start counting files that need to be
        # copied to this device.
        if device_start_index:
            copyfiles = copyfiles[device_start_index:]

        return copyfiles

    def _list_copyfiles(self, srcpaths):
        """
        Produces a list of all files that will be copied.

        Args:
            srcpaths (list):
            output (str):

        Returns:

            .. code-block:: python

                [
                    {
                        'src': '/src/path',
                        'dst': '/dst/path',
                        'bytes': 1024,
                        'index': 0,
                    },
                    ...
                ]

        """
        copyfiles = []  # [{'src': '/src/path', 'dst':'/dst/patht', 'bytes':1024}]
        for srcpath in srcpaths:
            srcpath = os.path.abspath(srcpath)

            for (root, dirnames, filenames) in os.walk(srcpath, topdown=True):
                for filename in filenames:
                    filepath = os.path.abspath('{}/{}'.format(root, filename))
                    relpath = filepath[len(srcpath) + 1:]
                    copyfiles.append({
                        'src':      filepath,
                        'dst':      os.path.abspath('{}/{}'.format(self.options.output, relpath)),
                        'relpath':  relpath,
                        'bytes':    os.path.getsize(filepath),
                    })

        # sort alphabetically by src
        copyfiles.sort(key=lambda x: x['src'])

        # add index
        for i in range(len(copyfiles)):
            copyfiles[i]['index'] = i

        # convert to a tuple of namedtuples.
        # (list[dict] consumes lots of memory)
        return tuple([multivolumecopy.copyfile.CopyFile(**kwargs) for kwargs in copyfiles])


