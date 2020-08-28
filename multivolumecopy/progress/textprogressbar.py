from __future__ import absolute_import
from __future__ import division
from __future__ import print_function


class TextProgressBar(object):
    """ Calculates/Renders a progressbar made of text-characters.
    """
    def __init__(self, width=None, char=None):
        """
        Args:
            width (int, optional):
                the width of your progressbar in text-characters.
        """
        self.width = width or 25
        self.char = char or '#'
        self._scale = int(100 / self.width)

        self._percent = 0.0
        self._completed_steps = 0
        self._remaining_steps = 0

    def __str__(self):
        return self.format()

    @property
    def percent(self):
        return self._percent

    @property
    def steps_completed(self):
        return self._completed_steps

    @property
    def steps_remaining(self):
        return self._remaining_steps

    def update(self, index, lastindex):
        if lastindex == 0:
            self._percent = 0.0
            self._completed_steps = 0
            self._remaining_steps = self.width
        else:
            self._percent = (index / lastindex) * 100
            self._completed_steps = int(self._percent / self._scale)
            self._remaining_steps = int(self.width - self._completed_steps)

    def format(self):
        return '{}{}'.format((self.char * self.steps_completed),
                             (' ' * self.steps_remaining))

    def render(self):
        print('\r{}'.format(self.format()))
