import logging
import select
import multiprocessing
import multiprocessing.managers
import queue
import sys
from multivolumecopy import filesystem
from multivolumecopy.copiers import copier
from multivolumecopy.progress import lineformatter
from multivolumecopy.prompts import commandlineprompt
from multivolumecopy.commands import interpreter
from multivolumecopy.reconcilers import keepfilesreconciler


logger = logging.getLogger(__name__)


WINDOWS_DISKFULL_ERRNO = 39
POSIX_DISKFULL_ERRNO = 28


class MultiProcessCopier(copier.Copier):
    """ Performs file copies using multiple threads (faster).

    Notes:
        * Memory issues with last version. Isolating copyjobs
          into processes makes it easier clean up after them.
    """
    def __init__(self, resolver, options=None):
        """
        Args:
            resolver (resolver.Resolver):
                Resolver, determines files to be copied.

            output (str): ``(ex: '/mnt/backup' )``
                The directory you'd like to backup to.

            options (CopyOptions, None):
                Options to use while performing copy
        """
        super(MultiProcessCopier, self).__init__(resolver, options)

        # NOTE: queueing using multiprocessing.Manager.list() to approximate LIFO queue.
        #       (for backup-file reconciliation, order must remain consistent in queue)
        #       (LIFO allows us to re-enqeueue failed copies due to diskfull error)

        # queues/locks
        self._mpmanager = multiprocessing.Manager()
        self._joblist = self._mpmanager.list()
        self._completed_queue = multiprocessing.Queue()
        self._error_queue = multiprocessing.Queue()
        self._started_queue = multiprocessing.Queue()
        self._device_full_lock = multiprocessing.Event()

        # components
        self._prompt = commandlineprompt.CommandlinePrompt()
        self._interpreter = interpreter.Interpreter()
        self._manager = _MultiProcessCopierWorkerManager(self._joblist,
                                                         self._started_queue,
                                                         self._completed_queue,
                                                         self._error_queue,
                                                         self._device_full_lock, options)
        self._progress_formatter = lineformatter.LineFormatter()
        self._reconciler = keepfilesreconciler.KeepFilesReconciler(resolver, options)

        # internal data
        self._copyfiles = []
        self._copied_indexes = []
        self._error_indexes = []
        self._started_indexes = []

    def start(self, device_start_index=None, start_index=None):
        """ Copies files, prompting for new device when device is full.

        Example:
            ::

                 (HDD-1)       (HDD-2)
               +---------+   +---------+
               |0  .. 100|   |101.. 250|    device_start_index (101)
               |         |   |         |       HDD-1 files do not belong on HDD-2
               |         |   |         |       0-100 will be deleted in reconciliation
               +---------+   +---------+       (but not 101-219)

               |----------------->220       start_index
                                               indicates where we start copying
                                               files from. We assume 101-219 are
                                               already present on disk.

        Args:
            device_start_index (int, optional):
                Determines the first index that should be copied to the device.
                (affects files that get deleted during reconciliation before backup)

            start_index (int, optional):
                Determines which files get queued for copying.
                Does not affect reconcliation.
        """
        # where to copy from
        start_index = start_index or device_start_index or 0

        self._copyfiles = self.resolver.get_copyfiles()
        self._setup_copied_indexes(device_start_index)
        self.write_jobfile(self._copyfiles)

        # only queue copyfiles after startindex
        for copyfile in self._copyfiles[start_index:]:
            self._joblist.append(copyfile)

        # before we start, we reconcile using the `device_start_index`
        # then adjust copied_indexes to match `start_index` so that
        # `copy_finished` works.
        self._reconciler.reconcile(self._copyfiles, self._copied_indexes)
        self._setup_copied_indexes(start_index)

        # begin eventloop
        self._mainloop()

    def _mainloop(self):
        try:
            while True:
                # render 0% progress
                self._render_progress()
                self._interpreter.eval_user_commands()

                # workers periodically die to release their memory. build as-needed
                self._manager.build_workers()

                self._evaluate_queues()
                self._evaluate_diskfull_check()

                if self.copy_finished():
                    print('Successfully Copied {} Files'.format(len(self._copyfiles)))
                    return True

        finally:
            self._manager.stop()
            self._manager.join(timeout=3000)

    def _setup_copied_indexes(self, device_start_index):
        # affects which files get deleted during reconciliation.
        if not device_start_index:
            return
        self._copied_indexes = [x.index for x in self._copyfiles[:device_start_index]]

    def copy_finished(self):
        processed_files = len(self._copied_indexes) + len(self._error_indexes)
        return processed_files == len(self._copyfiles)

    def _evaluate_queues(self):
        self._evaluate_started_queue()
        self._evaluate_error_queue()
        self._evaluate_completed_queue()

    def _evaluate_started_queue(self):
        while True:
            try:
                data = self._started_queue.get(timeout=0)
                self._started_indexes.append(data.index)
            except queue.Empty:
                return

    def _evaluate_completed_queue(self):
        while True:
            try:
                filedata = self._completed_queue.get(timeout=0)
                self._try_remove_started_index(filedata.index)
                self._copied_indexes.append(filedata.index)
                self._render_progress(filedata=filedata)
            except queue.Empty:
                return

    def _evaluate_error_queue(self):
        while True:
            try:
                filedata = self._error_queue.get(timeout=0)
                self._try_remove_started_index(filedata.index)
                self._error_indexes.append(filedata.index)
                self._render_progress(filedata=filedata)
            except queue.Empty:
                return

    def _evaluate_diskfull_check(self):
        if self._device_full_lock.is_set():
            # request stop, wait for all workers to finish current file
            self._manager.stop()
            self._manager.join()

            # copy operation may finish before we have updated screen/counters
            self._evaluate_queues()

            # now that workers are stopped, check again we aren't done.
            if self.copy_finished():
                return

            # retrieve/requeue wip files, and prompt user to switch devices
            self._empty_and_requeue_started_copyfiles()
            # TODO: verify no extra files on disk (if reconciliation was inaccurate due to compression etc)
            # TODO: should be able to just re-use reconcile() and check freed space.
            self._prompt_diskfull()
            self._reconciler.reconcile(self._copyfiles, self._copied_indexes)
            self._device_full_lock.clear()
            return 0

    def _empty_and_requeue_started_copyfiles(self):
        """
        """
        sorted_started_indexes = sorted(self._started_indexes)
        requeued = 0
        while len(self._started_indexes) > 0:
            index = sorted_started_indexes.pop(0)
            self._try_remove_started_index(index)
            self._joblist.insert(0, self._copyfiles[index])
            requeued += 1

        if requeued:
            print('')
            logger.info('{} files have been requeued'.format(requeued))

    def _render_progress(self, filedata=None):
        msg = self._progress_formatter.format(len(self._copied_indexes), len(self._copyfiles), self._error_indexes, filedata)
        sys.stdout.write(msg)

    def _prompt_diskfull(self):
        """ Loop request to continue/decline until valid response from user.

        Args:
            requeued_indexes (list): ``(ex: [100, 104, 102])``
                the tasks that will be requeued.
        """
        while True:
            print('\nMounted Device is full. '
                  'Please mount a new device, and press "c" to continue. \n'
                  '  (output: "{}")\n'
                  .format(filesystem.get_mount(self.options.output)))

            print('(Or press "q" to abort)')
            print('')

            command = self._prompt.input('> ')
            if command in ('c', 'C'):
                return

            if command in ('q', 'Q'):
                print('Aborted by user')
                sys.exit(1)

    def _try_remove_started_index(self, index):
        try:
            self._started_indexes.remove(index)
        except(ValueError):
            pass


class _MultiProcessCopierWorkerManager(object):
    """ Manages worker processes, restarting them
    automatically when they exit (while iterating through this object).
    """
    def __init__(self, joblist, started_queue, completed_queue, error_queue, device_full_lock, options):
        self._workers = []
        self._joblist = joblist
        self._completed_queue = completed_queue
        self._started_queue = started_queue
        self._error_queue = error_queue

        self._device_full_lock = device_full_lock
        self._options = options

    @property
    def options(self):
        return self._options

    def __iter__(self):
        """ iter workers, cleaning up old
        """
        for i in reversed(range(len(self._workers))):
            worker = self._workers[i]
            if worker.is_alive():
                yield worker
            else:
                self._workers.remove(worker)
                worker.close()

    def build_workers(self):
        """ Builds workers until number of active workers matches `options.num_workers`
        """
        while True:
            if self.active_workers() < self.options.num_workers:
                worker = _MultiProcessCopierWorker(self._joblist,
                                                   self._started_queue,
                                                   self._completed_queue,
                                                   self._error_queue,
                                                   self._device_full_lock,
                                                   maxtasks=self.options.max_worker_tasks)
                self._workers.append(worker)
                worker.start()
            else:
                break

    def active_workers(self):
        return len(list(filter(lambda x: x.is_alive(), self.__iter__())))

    def stop(self):
        logger.debug('Stopping Workers...')
        # worker can only process a single queue item at a time.
        # please wait afterwards.
        for i in range(self.options.num_workers):
            self._joblist.insert(0, None)

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


class _MultiProcessCopierWorker(multiprocessing.Process):
    """ Performs copy on files added to the queue.
    Runs until it's lifespan is reached, or it receives a poison pill from the queue.
    """
    def __init__(self, joblist, started_queue, completed_queue, error_queue, device_full_event, maxtasks=50, *args, **kwargs):
        super(_MultiProcessCopierWorker, self).__init__(*args, **kwargs)

        self._joblist = joblist
        self._started_queue = started_queue
        self._completed_queue = completed_queue
        self._error_queue = error_queue
        self._device_full_event = device_full_event

        self._maxtasks = maxtasks

    def run(self):
        loop_count = 0
        while loop_count < self._maxtasks:
            import time
            time.sleep(4)

            # device lock being set also acts like a poison pill
            if self._device_full_event.is_set():
                logger.debug('Process Exit, device full')
                return

            # try retrieving next item from list, loop if unavailable
            try:
                data = self._joblist.pop(0)
            except IndexError:
                continue

            # `None` is poison pill, causing exit
            if data is None:
                return

            # inform wip queue that job started
            self._started_queue.put(data)

            # otherwise data is a single copyfile dict.
            try:
                filesystem.copyfile(src=data.src, dst=data.dst, reraise=True, log_errors=False)
                filesystem.copyfilestat(src=data.src, dst=data.dst)
                self._completed_queue.put(data)
            except(OSError) as exc:
                if not self._exception_indicates_device_full(exc):
                    self._error_queue.put(data)
                    raise
                self._device_full_event.set()
                return

            # increment loop count, so we can kill worker, and release memory
            loop_count += 1

        logger.debug('Worker maxtasks reached. Exiting')

    def _exception_indicates_device_full(self, os_error):
        """
        Args:
            os_error (OSError): the raised exception we are checking
        """
        if sys.platform.startswith('win'):
            if os_error.winerror == WINDOWS_DISKFULL_ERRNO:
                return True
        else:
            if os_error.errno == POSIX_DISKFULL_ERRNO:
                return True
        return False


