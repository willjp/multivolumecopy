#!/usr/bin/env python
"""
checks operating system running maya so adjustments can be made to paths and
environment
"""
# builtin
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
import argparse
import sys
# package
from multivolumecopy import mvcopy
# external
# internal


class CommandlineInterface(object):
    def __init__(self):
        self.parser = argparse.ArgumentParser(
            description='Simple Multi-Volume file copy tool. You will be prompted when the medium is full.'
        )

        self.parser.add_argument(
            'srcpaths', nargs='+', help='List of filepaths to copy'
        )

        self.parser.add_argument(
            '--padding', help='Room to leave on each backup disk before prompting for a new disk',
            metavar='5M',
            default=None,
            type=str,
        )

        self.parser.add_argument(
            '-o', '--output', help='The path you\'d like to write backups to'
        )

    def parse_args(self):
        args = self.parser.parse_args()

        if not args.output:
            print('-o/--output flag is mandatory')
            sys.exit(1)

        if not args.srcpaths:
            print('No srcpaths specified to copy')
            sys.exit(1)

        mvcopy.mvcopy(
            srcpaths=args.srcpaths,
            output=args.output,
            device_padding=args.padding,
        )

    @staticmethod
    def show():
        c = CommandlineInterface()
        c.parse_args()


if __name__ == '__main__':
    cli = CommandlineInterface()
    cli.parse_args()
