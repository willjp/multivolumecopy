from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
import abc


class CommandBase(object):
    """ Interface for commands
    """
    __metaclass__ = abc.ABCMeta

    #: hotkey used to execute command
    #: ex: 'm'
    HOTKEY = None

    def execute(self):
        """ Execute the command.
        """
        raise NotImplementedError()
