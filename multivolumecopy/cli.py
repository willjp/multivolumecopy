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
            description=('Simple Multi-Volume file copy tool. You will be prompted to replace device '
                         'when the medium is full.')
        )

        self.parser.add_argument(
            'srcpaths', nargs='+', help='List of filepaths to copy'
        )
        self.parser.add_argument(
            '-f', '--jobfile', help='Continue a pre-existing mvcopy job that was interrupted. (also see --start-index)',
            metavar='/path/to/mvcopy-jobdata.json'
        )
        self.parser.add_argument(
            '-i', '--start-index', help='Index you\'d like to begin copying from. Ignored if using srcpaths.',
            metavar='533',
            type=int,
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

        # validate arguments
        if not args.output:
            print('-o/--output flag is mandatory')
            sys.exit(1)

        if not args.srcpaths and not args.jobfile:
            print('No srcpaths or jobfile specified to copy')
            sys.exit(1)

        # begin copying
        common_kwargs = dict(
            output=args.output,
            device_padding=args.device_padding,
        )

        if args.jobfile:
            if args.srcpaths:
                print('Print jobfile specified, so srcpaths will be ignored: {}'.format(repr(args.srcpaths)))
            mvcopy.mvcopy_jobfile(args.jobfile, index=args.index, **common_kwargs)
        elif args.srcpaths:
            mvcopy.movcopy_srcpaths(args.srcpaths, **common_kwargs)


if __name__ == '__main__':
    cli = CommandlineInterface()
    cli.parse_args()
