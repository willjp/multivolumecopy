""" foo
"""
import logging
import multiprocessing
import pprint
import queue
import sys
from multivolumecopy import filesystem
from multivolumecopy.copiers import copier
from multivolumecopy.progress import simpleprogressformatter
from multivolumecopy.prompts import commandlineprompt


logger = logging.getLogger(__name__)


class MemSafeCopier(copier.Copier):
    """

    Notes:
        * Memory issues with last version. Isolating copy jobs into processes
          that are easier to clean up .
    """

    def __init__(self, source, options=None):
        """
        Args:
            source (resolver.Resolver):
                CopySource object, determines files to be copied.

            output (str): ``(ex: '/mnt/backup' )``
                The directory you'd like to backup to.

            options (CopyOptions, None):
                Options to use while performing copy
        """
        super(MemSafeCopier, self).__init__(source, options)

        # queues/locks
        self._queue = multiprocessing.Queue()
        self._progress_queue = multiprocessing.Queue()
        self._wip_queue = multiprocessing.Queue()
        self._device_full_lock = multiprocessing.Event()

        # components
        self._prompt = commandlineprompt.CommandlinePrompt()
        self._manager = ProcessManager(self._queue, self._wip_queue, self._progress_queue, self._device_full_lock, options)
        self._progress_formatter = simpleprogressformatter.SimpleProgressFormatter()

        # internal data
        self._copied_files = 0
        self._total_files = 0
        self._wip_filedata = []

    def start(self):
        """ Copies files, prompting for new device when device is full.
        """
        copyfiles = self.source.get_copyfiles()
        self._total_files = len(copyfiles)
        for copyfile in copyfiles:
            self._queue.put(copyfile)

        try:
            while True:
                # render 0% progress
                self._render_progress()

                # workers periodically die to release their memory. build as-needed
                self._manager.build_workers()

                self._evaluate_wip_queue()
                self._evaluate_progress_queue()
                self._evaluate_diskfull_check()
                if self._copied_files == self._total_files:
                    print('Successfully Copied {} Files'.format(self._total_files))
                    self._manager.stop()
                    self._manager.join()
                    return

        finally:
            self._manager.stop()
            self._manager.join(timeout=3000)

    def _evaluate_wip_queue(self):
        while True:
            try:
                data = self._wip_queue.get(timeout=0)
                self._wip_filedata.append(data)
            except queue.Empty:
                return

    def _evaluate_progress_queue(self):
        while True:
            try:
                filedata = self._progress_queue.get(timeout=0)
                self._copied_files += 1
                self._render_progress(filedata=filedata)
            except queue.Empty:
                return

    def _evaluate_diskfull_check(self):
        if self._device_full_lock.is_set():
            # request stop, wait for all workers to finish current file
            self._manager.stop()
            self._manager.join()

            # retrieve/requeue wip files, and prompt user to switch devices
            indexes = self._empty_and_requeue_wip_copyfiles()
            self._prompt_diskfull(indexes)
            self._device_full_lock.clear()

    def _empty_and_requeue_wip_copyfiles(self):
        """
        """
        wip_filedata = []
        while len(self._wip_filedata) > 0:
            filedata = self._wip_filedata.pop(0)
            wip_filedata.append(filedata)
            self._queue.put(filedata)
        return wip_filedata

    def _render_progress(self, filedata=None):
        msg = self._progress_formatter.format(self._copied_files, self._total_files, filedata)
        sys.stdout.write(msg)

    def _prompt_diskfull(self, requeue_indexes):
        """ Loop request to continue/decline until valid response from user.

        Args:
            requeued_indexes (list): ``(ex: [100, 104, 102])``
                the tasks that will be requeued.
        """
        while True:
            print('')

            if requeue_indexes:
                print('The following files have been requeued: {}\n'.format(pprint.pprint(requeue_indexes)))

            print('Next index "{}": {}\n'.format(self._copied_files, self.options.jobfile))

            print('Mounted Device is full. '
                  'Please mount a new device, and press "c" to continue. "{}"'
                  .format(filesystem.get_mount(self.options.output)))

            print('(Or press "q" to abort)')
            print('')

            command = self._prompt.input('> ')
            if command in ('c', 'C'):
                return

            if command in ('q', 'Q'):
                print('Aborted by user')
                sys.exit(1)


class ProcessManager(object):
    def __init__(self, queue, wip_queue, progress_queue, device_full_lock, options):
        self._workers = []
        self._queue = queue
        self._progress_queue = progress_queue
        self._wip_queue = wip_queue

        self._device_full_lock = device_full_lock
        self._options = options

    @property
    def options(self):
        return self._options

    def build_workers(self):
        """ Builds workers until number of active workers matches `options.num_workers`
        """
        while True:
            active_workers = len(list(filter(lambda x: x.is_alive(), self._workers)))
            if active_workers < self.options.num_workers:
                worker = MemSafeCopierWorker(self._queue, self._wip_queue, self._progress_queue, self._device_full_lock)
                self._workers.append(worker)
                worker.start()
            else:
                break

    def stop(self):
        logger.debug('Stopping Workers...')
        # worker can only process a single queue item at a time.
        # please wait afterwards.
        for i in range(self.options.num_workers):
            self._queue.put(None)

    def terminate(self):
        logger.debug('Force Terminating Workers...')
        # please request stop first.
        # please wait afterwards.
        for worker in self._workers:
            if not worker.is_alive():
                continue
            worker.terminate()

    def join(self, timeout=None):
        for worker in self.__iter__():
            if not worker.is_alive():
                continue
            worker.join(timeout)

    def __iter__(self):
        """ iter workers, cleaning up old
        """
        for i in reversed(range(len(self._workers))):
            worker = self._workers[i]
            if worker.is_alive():
                yield worker
            else:
                self._workers.remove(worker)


class MemSafeCopierWorker(multiprocessing.Process):
    """ Processes queue items (copy files) forever until poison pill is received.
    """
    def __init__(self, queue, wip_queue, progress_queue, device_full_lock, maxtasks=50, *args, **kwargs):
        super(MemSafeCopierWorker, self).__init__(*args, **kwargs)
        self._queue = queue
        self._wip_queue = wip_queue
        self._progress_queue = queue
        self._maxtasks = maxtasks
        self._device_full_lock = device_full_lock

    def run(self):
        i = 0
        while i < self._maxtasks:
            # device lock being set also acts like a poison pill
            if self._device_full_lock.set():
                return

            data = self._queue.get()

            # inform wip queue that job started
            self._wip_queue.put(data)

            # `None` is poison pill, causing exit
            if data is None:
                return

            # otherwise data is a single copyfile dict.
            try:
                filesystem.copyfile(src=data['src'], dst=data['dst'], reraise=True, log_errors=False)
                filesystem.copyfilestat(src=data['src'], dst=data['dst'])
                self._progress_queue.put(data)
            except(OSError):
                self._device_full_lock.set()

