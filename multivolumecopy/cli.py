#!/usr/bin/env python
"""
checks operating system running maya so adjustments can be made to paths and
environment
"""
# builtin
from __future__ import absolute_import, division, print_function
import argparse
import logging
import sys
# package
from multivolumecopy import mvcopy
# external
# internal


class CommandlineInterface(object):
    def __init__(self):
        self.parser = argparse.ArgumentParser(
            description=('Simple Multi-Volume file copy tool. You will be prompted to replace device '
                         'when the medium is full. (ex: multivolumecopy /path/src -o /path/dst)')
        )

        # new job
        self.parser.add_argument(
            'srcpaths', nargs='+', help='List of filepaths to copy'
        )

        # continue job
        self.parser.add_argument(
            '-f', '--jobfile', help='Continue a pre-existing mvcopy job that was interrupted. (also see --start-index)',
            metavar='/path/to/mvcopy-jobdata.json'
        )
        self.parser.add_argument(
            '-i', '--start-index', help='Index you\'d like to begin copying from. Ignored if using srcpaths.',
            metavar='533',
            type=int,
        )

        # misc
        self.parser.add_argument(
            '--device-padding', help='Room to leave on each backup disk before prompting for a new disk',
            metavar='5M',
            default=None,
            type=str,
        )
        self.parser.add_argument(
            '--no-progress', help='Do not show a progressbar',
            action='store_true',
        )
        self.parser.add_argument(
            '-o', '--output', help='The path you\'d like to write backups to'
        )

        # logging
        self.parser.add_argument('-v', '--verbose', action='store_true', help='verbose logging')
        self.parser.add_argument('-vv', '--very-verbose', action='store_true', help='very verbose logging')

    def parse_args(self):
        args = self.parser.parse_args()

        # validate arguments
        if not args.output:
            print('-o/--output flag is mandatory')
            sys.exit(1)

        if not args.srcpaths and not args.jobfile:
            print('No srcpaths or jobfile specified to copy')
            sys.exit(1)

        # logging setup
        log_level = logging.WARNING
        if args.very_verbose:
            log_level = logging.DEBUG
        elif args.verbose:
            log_level = logging.INFO
        logging.basicConfig(level=log_level, format='%(levelname)s| %(msg)s')

        # begin copying
        common_kwargs = dict(
            output=args.output,
            device_padding=args.device_padding,
            no_progressbar=args.no_progress,
        )

        if args.jobfile:
            if args.srcpaths:
                print('Print jobfile specified, so srcpaths will be ignored: {}'.format(repr(args.srcpaths)))
            mvcopy.mvcopy_jobfile(args.jobfile, index=args.index, **common_kwargs)
        elif args.srcpaths:
            mvcopy.mvcopy_srcpaths(args.srcpaths, **common_kwargs)


if __name__ == '__main__':
    cli = CommandlineInterface()
    cli.parse_args()
