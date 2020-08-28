import fnmatch
import pprint
import tracemalloc
try:
    import ipdb as pdb
except(ImportError):
    import pdb
from multivolumecopy.commands import commandbase


class MemStats(commandbase.CommandBase):
    """ Prints memory changes since last snapshot,
    and runs pdb so you can dynamically inspect memory issues.
    """
    HOTKEY = 'm'

    SNAPSHOT = None
    LAST_SNAPSHOT = None

    def __init__(self):
        tracemalloc.start()
        self._filters = [tracemalloc.Filter(False, "<frozen importlib._bootstrap>"),
                         tracemalloc.Filter(False, "<unknown>")]
        if MemStats.LAST_SNAPSHOT is None:
            MemStats.LAST_SNAPSHOT = tracemalloc.take_snapshot().filter_traces(self._filters)

        super(MemStats, self).__init__()

    def execute(self):
        MemStats.SNAPSHOT = tracemalloc.take_snapshot().filter_traces(self._filters)

        # descending list of processes with largest change in memory consumption
        raw_stats = self.SNAPSHOT.compare_to(self.LAST_SNAPSHOT, 'lineno')
        stats = raw_stats.filter_traces(tracemalloc.Filter(False, "<frozen importlib._bootstrap>"),
                                        tracemalloc.Filter(False, "<unknown>"))
        #stats = list(filter(lambda x: fnmatch.fnmatch(x.traceback[0].filename, '*/multivolumecopy/*'), stats))
        stats = sorted(stats, key=lambda x: x.size, reverse=True)

        # 'top' style preview, and pdb for investigation
        print('----------------------')
        pprint.pprint(list(stats[:10]))
        print('----------------------')
        print('ex: print(stats[0])  # highest memory consumption')
        pdb.set_trace()

        self.LAST_SNAPSHOT = self.SNAPSHOT
