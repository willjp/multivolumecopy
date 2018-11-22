#!/usr/bin/env python
# builtin
from __future__ import unicode_literals
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
# package
import multivolumecopy
# external
import setuptools
# internal


__version__ = multivolumecopy.__version__

if __version__.endswith(('a', 'b')):
    raise RuntimeError(
        'You are trying to install/release an alpha/beta version of software'
    )


if __name__ == '__main__':
    setuptools.setup(
        name='multivolumecopy',
        version=__version__,
        author='Will Pittman',
        license='BSD',
        packages=setuptools.find_packages(exclude=['tests/*']),
        test_requires=[
            'setuptools',
        ],
    )
