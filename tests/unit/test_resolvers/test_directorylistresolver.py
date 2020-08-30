import os
import pytest
from multivolumecopy import copyoptions
from multivolumecopy.resolvers import directorylistresolver
from testhelpers import multiprocessinghelpers
import mock


NS = directorylistresolver.__name__


class TestDirectoryListResolver:
    def setup(self):
        self.options = copyoptions.CopyOptions()
        self.options.output = '/dst'

        self.resolver = directorylistresolver.DirectoryListResolver(['/src'], self.options)

    def test_sets_relpath_for_files_at_root(self):
        walk_paths = {'/src': [('/src', [], ['a.txt'])]}
        self.resolver.options.output = '/dst'
        copyfiles = self.get_copyfiles(self.resolver, walk_paths)
        assert copyfiles[0].relpath == 'a.txt'

    def test_sets_relpath_for_files_in_subdirs(self):
        walk_paths = {'/src': [('/src', ['a'], []), ('/src/a', [], ['b.txt'])]}
        self.resolver.options.output = '/dst'
        copyfiles = self.get_copyfiles(self.resolver, walk_paths)
        assert copyfiles[0].relpath == 'a/b.txt'

    def test_sets_dst_for_files_at_root(self):
        walk_paths = {'/src': [('/src', [], ['a.txt'])]}
        self.resolver.options.output = '/dst'
        copyfiles = self.get_copyfiles(self.resolver, walk_paths)
        assert copyfiles[0].dst == '/dst/a.txt'

    def test_sets_dst_for_files_in_subdirs(self):
        walk_paths = {'/src': [('/src', ['a'], []), ('/src/a', [], ['b.txt'])]}
        copyfiles = self.get_copyfiles(self.resolver, walk_paths)
        assert copyfiles[0].dst == '/dst/a/b.txt'

    def test_sets_src_for_files_at_root(self):
        walk_paths = {'/src': [('/src', [], ['a.txt'])]}
        copyfiles = self.get_copyfiles(self.resolver, walk_paths)
        assert copyfiles[0].src == '/src/a.txt'

    def test_sets_src_for_files_at_root(self):
        walk_paths = {'/src': [('/src', ['a'], []), ('/src/a', [], ['b.txt'])]}
        copyfiles = self.get_copyfiles(self.resolver, walk_paths)
        assert copyfiles[0].src == '/src/a/b.txt'

    def test_sets_bytes(self):
        walk_paths = {'/src': [('/src', ['a'], []), ('/src/a', [], ['b.txt'])]}
        copyfiles = self.get_copyfiles(self.resolver, walk_paths)
        assert copyfiles[0].bytes == 1024

    def test_sets_index(self):
        walk_paths = {'/src': [('/src', ['a'], ['a.txt']), ('/src/a', [], ['b.txt'])]}
        copyfiles = self.get_copyfiles(self.resolver, walk_paths)
        indexes = [x.index for x in copyfiles]
        assert indexes == [0, 1]

    def test_result_sorted_alphabetical_by_src(self):
        walk_paths = {'/src': [
            ('/src', ['a', 'b'], ['1.txt']),
            ('/src/b', [], ['2.txt']),
            ('/src/a', [], ['3.txt']),
        ]}
        copyfiles = self.get_copyfiles(self.resolver, walk_paths)
        indexes = [x.src for x in copyfiles]
        assert indexes == ['/src/1.txt', '/src/a/3.txt', '/src/b/2.txt']

    def test_merges_multiple_sources(self):
        resolver = directorylistresolver.DirectoryListResolver(['/src/a', '/src/b'], self.options)
        walk_paths = {
            '/src/a': [('/src/a', ['a'], ['1.txt']),
                       ('/src/a/b', [], ['2.txt'])],
            '/src/b': [('/src/b', ['c'], ['1.txt']),
                       ('/src/b/c', [], ['2.txt'])],
        }
        copyfiles = self.get_copyfiles(resolver, walk_paths)
        indexes = [x.src for x in copyfiles]
        expected = ['/src/a/1.txt',
                    '/src/a/b/2.txt',
                    '/src/b/1.txt',
                    '/src/b/c/2.txt']
        # NOTE: indexes should already be sorted, here we are ignoring
        #       that implementation, and checking the merged files only.
        assert sorted(indexes) == expected

    def get_copyfiles(self, resolver, walk_paths):
        """ Runs the test.

        Args:
            srcpath_walk (dict):
                dictionary of searchdirs, and lists of `root, dirnames, filenames`
                that should be returned during each iteration.

                .. code-block:: python

                    {
                        '/src': [
                            ('/src', ['A'], ['a.txt', 'b.txt']),
                            ('/src/A', [], ['c.txt']),
                            (...),
                            ...
                        ],
                        ...
                    }

            dstdir (str): ``(ex: '/dst/')``
                where file is copied to.

        """
        def walk_results(srcpath, *args, **kwargs):
            for copyfile in walk_paths[srcpath]:
                yield copyfile

        with mock.patch('{}.os.path.getsize'.format(NS), return_value=1024):
            with mock.patch('{}.os.walk'.format(NS), side_effect=walk_results):
                with mock.patch.object(os, 'getcwd', return_value='/var/tmp'):
                    with multiprocessinghelpers.mock_pool():
                        return resolver.get_copyfiles()

