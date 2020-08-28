from multivolumecopy.commands import commandbase, memstats
import sys
import select


class Interpreter(object):
    """ Evaluates hotkeys while program is running.
    (unfortunately requires 'Enter')

    Notes:
        hacky, mostly here for debugging.
    """
    def __init__(self):
        self._commands = [memstats.MemStats()]

    def eval_user_commands(self):
        # nothing to evaluate if no commands present
        if not self._commands:
            return

        # windows cannot select on file like objects
        if sys.platform.startswith('win'):
            return

        # retrieve key, execute comman dif available
        (readable, _, _) = select.select([sys.stdin], [], [], 0.2)
        if readable:
            char = readable[0].read(1)
            for cmd in self._commands:
                if cmd.HOTKEY == char:
                    return cmd.execute()
            print('Unknown comand: {}'.format(char))
