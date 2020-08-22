from multivolumecopy.resolvers import resolver
import os


class DirectoryListResolver(resolver.Resolver):
    """ Read copyfile src/dst determined by a list of source directories,
    and a single output dir.
    """
    def __init__(self, directories, options):
        """
        Args:
            srcpaths (list): ``(ex: ['/mnt/movies', '/mnt/music', ...])``
                A list of directories that you'd like to backup.
        """
        super(DirectoryListResolver, self).__init__()
        self._directories = directories
        self._options = options

    def get_copyfiles(self):
        srcpaths = sorted([os.path.expanduser(p) for p in self._directories])
        copyfiles = self._list_copyfiles(srcpaths)
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
                        'dst':      os.path.abspath('{}/{}'.format(self._options.output, relpath)),
                        'relpath':  relpath,
                        'bytes':    os.path.getsize(filepath),
                    })
        copyfiles.sort(key=lambda x: x['src'])

        return copyfiles


