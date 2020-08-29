import collections


CopyFile = collections.namedtuple('CopyFile', ('src', 'dst', 'relpath', 'bytes', 'index'))
