from multivolumecopy.resolvers import resolver
import json


class JobFileResolver(resolver.Resolver):
    """ Read copyfile src/dst from a JSON jobfile.

    Example:

        Sample ``mvcopy-jobdata.json``

        .. code-block:: json

            [
                {"src": "/src/a.txt", "dst": "/dst/a.txt", "relpath": "a.txt", "bytes": 1000, "index": 0},
                {"src": "/src/b.txt", "dst": "/dst/b.txt", "relpath": "b.txt", "bytes": 1000, "index": 1},
                {"src": "/src/c.txt", "dst": "/dst/c.txt", "relpath": "c.txt", "bytes": 1000, "index": 2},
                {"src": "/src/d.txt", "dst": "/dst/d.txt", "relpath": "d.txt", "bytes": 1000, "index": 3},
                {"src": "/src/e.txt", "dst": "/dst/e.txt", "relpath": "e.txt", "bytes": 1000, "index": 4}
            ]

    """
    def __init__(self, filepath, options):
        super(JobFileResolver, self).__init__(options)
        self._filepath = filepath

    def get_copyfiles(self, device_start_index=None, start_index=None):
        with open(self._filepath, 'r') as fd:
            copyfiles = json.loads(fd.read())
        return copyfiles


