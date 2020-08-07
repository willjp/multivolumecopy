#!/usr/bin/env python
import glob
import multivolumecopy
import os
import setuptools


__version__ = multivolumecopy.__version__


if __version__.endswith(('a', 'b')):
    msg = 'You are trying to install/release an alpha/beta version of software'
    raise RuntimeError(msg)


def get_zsh_completionpath():
    paths = (
        '/usr/local/share/zsh/functions/Completion/Unix',
        '/usr/local/share/zsh/*/functions/Completion/Unix',
        '/usr/share/zsh/functions/Completion/Unix',
    )
    for path in paths:
        matches = glob.glob(path)
        if not matches:
            continue
        if os.path.isdir(matches[0]):
            return path[0]
    msg = 'No fpath could be found for installation in: %s' % repr(paths)
    print('[WARNING] unable to install zsh completion function')


def get_data_files():
    zsh_completionpath = get_zsh_completionpath()
    if zsh_completionpath:
        return [('{}/_multivolumecopy'.format(zsh_completionpath), ['data/autocomplete.zsh/_multivolumecopy'])]
    return []


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
                'multivolumecopy=multivolumecopy.cli:CommandlineInterface.exec_',
            ],
        },
        data_files=get_data_files(),
        setup_requires=[
            'setuptools',
        ],
        tests_require=[
            'pytest',
            'pytest-runner',
            'mock<4',  # mock 4+ currently has invalid syntax for py27
        ],
    )
