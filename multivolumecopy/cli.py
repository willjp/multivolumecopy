#!/usr/bin/env python
""" Commandline interface.
"""
from __future__ import absolute_import, division, print_function
import argparse
import logging
import sys
from multivolumecopy.resolvers import directorylistresolver, jobfileresolver
from multivolumecopy import copyoptions
from multivolumecopy.copiers import simplecopier, memsafecopier


class CommandlineInterface(object):
    @classmethod
    def exec_(cls):
        cli = CommandlineInterface()
        cli.parse_args()

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
            '--hide-progress', help='Do not show a progressbar',
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
        self._validate_args(args)
        self._setup_logging(args)

        self._start(args)

    def _start(self, args):
        options = self._get_copyoptions_from_args(args)
        source = self._get_copysource_from_args(args, options)
        copier_ = simplecopier.SimpleCopier(source, options)
        #copier_ = memsafecopier.MemSafeCopier(source, options)

        copier_.start()

    def _validate_args(self, args):
        # validate arguments
        if not args.output:
            print('-o/--output flag is mandatory')
            sys.exit(1)

        if not args.srcpaths and not args.jobfile:
            print('No srcpaths or jobfile specified to copy')
            sys.exit(1)

    def _setup_logging(self, args):
        # logging setup
        log_level = logging.WARNING
        if args.very_verbose:
            log_level = logging.DEBUG
        elif args.verbose:
            log_level = logging.INFO
        logging.basicConfig(level=log_level, format='%(levelname)s| %(msg)s')

    def _get_copyoptions_from_args(self, args):
        options = copyoptions.CopyOptions()
        options.output = args.output
        options.device_padding = args.device_padding
        options.show_progressbar = not args.hide_progress
        return options

    def _get_copysource_from_args(self, args, options):
        if args.jobfile:
            return jobfileresolver.JobFileResolver(args.jobfile)
        if args.srcpaths:
            return directorylistresolver.DirectoryListResolver(args.srcpaths, options)
        raise NotImplementedError()


if __name__ == '__main__':
    cli = CommandlineInterface()
    cli.parse_args()
