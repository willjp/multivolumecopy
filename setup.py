#!/usr/bin/env python
# builtin
# package
import multivolumecopy
import os
# external
import setuptools
# internal


__version__ = multivolumecopy.__version__

if __version__.endswith(('a', 'b')):
    raise RuntimeError(
        'You are trying to install/release an alpha/beta version of software'
    )


def get_zsh_completionpath():
    paths = (
        '/usr/local/share/zsh/functions/Completion/Unix',
        '/usr/share/zsh/functions/Completion/Unix',
    )
    for path in paths:
        if os.path.isdir(path):
            return path
    raise RuntimeError(
        'No fpath could be found for installation in: %s' % repr(paths))


if __name__ == '__main__':
    setuptools.setup(
        name='multivolumecopy',
        version=__version__,
        author='Will Pittman',
		  author_email='willjpittman@gmail.com',
        license='MIT',
        packages=setuptools.find_packages(exclude=['tests/*']),
        entry_points={
            'console_scripts': [
                'multivolumecopy = multivolumecopy.cli:CommandlineInterface.show',
            ],
        },
        data_files=[
            (get_zsh_completionpath(), ['data/autocomplete.zsh/_multivolumecopy']),
        ],
        setup_requires=[
            'setuptools',
        ],
        test_requires=[
            'pytest',
            'mock',
        ],
    )
