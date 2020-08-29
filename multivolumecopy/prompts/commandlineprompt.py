from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
import sys


class CommandlinePrompt(object):
    """ Request input on the commandline.
    """
    def input(self, message):
        # python2
        if sys.version_info[0] < 3:
            reply = raw_input(message)
            return reply.encode('utf-8')

        # python3
        reply = input(message)
        if hasattr(reply, 'decode'):
            return reply.decode('utf-8')
        else:
            return reply
