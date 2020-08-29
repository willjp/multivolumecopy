#!/usr/bin/env python
import glob
import multivolumecopy
import os
import setuptools


__version__ = multivolumecopy.__version__


if __version__.endswith(('a', 'b')):
    msg = 'You are trying to install/release an alpha/beta version of software'
    raise RuntimeError(msg)


if __name__ == '__main__':
    setuptools.setup(
        name='multivolumecopy',
        version=__version__,
        author='Will Pittman',
        author_email='willjpittman@gmail.com',
        license='MIT',
        packages=setuptools.find_packages(exclude=['tests/*', 'testhelpers/*']),
        entry_points={
            'console_scripts': [
                'multivolumecopy=multivolumecopy.cli:CommandlineInterface.exec_',
            ],
        },
        setup_requires=['setuptools'],
    )
