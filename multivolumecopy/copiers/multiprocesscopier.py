from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
import logging
import multiprocessing
import multiprocessing.managers
import os
import queue
import sys
import time
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
    def __init__(self, resolver, options=None, reconciler=None):
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
        self.joblist = self._mpmanager.list()
        self.completed_queue = multiprocessing.Queue()
        self.error_queue = multiprocessing.Queue()
        self.started_queue = multiprocessing.Queue()
        self.device_full_lock = multiprocessing.Event()

        # components
        self.prompt = commandlineprompt.CommandlinePrompt()
        self._interpreter = interpreter.Interpreter()
        self.manager = _MultiProcessCopierWorkerManager(self.joblist,
                                                        self.started_queue,
                                                        self.completed_queue,
                                                        self.error_queue,
                                                        self.device_full_lock,
                                                        options)
        self._progress_formatter = lineformatter.LineFormatter()
        self.reconciler = reconciler or keepfilesreconciler.KeepFilesReconciler(resolver, options)

        # internal data
        self._copyfiles = []
        self._copied_indexes = []
        self._error_indexes = []
        self._started_indexes = []

    def start(self, device_start_index=None, start_index=None, maxloops=-1):
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

            maxloops (int):
                Exit after this many loops.
                Negative numbers loop infinitely.
                For testing.
        """
        # where to copy from
        start_index = start_index or device_start_index or 0

        self._copyfiles = self.resolver.get_copyfiles()
        self._setup_copied_indexes(device_start_index)
        self.write_jobfile(self._copyfiles)

        # only queue copyfiles after startindex
        for copyfile in self._copyfiles[start_index:]:
            self.joblist.append(copyfile)

        # before we start, we reconcile using the `device_start_index`
        # then adjust copied_indexes to match `start_index` so that
        # `copy_finished` works.
        self.reconciler.reconcile(self._copyfiles, self._copied_indexes)
        self._setup_copied_indexes(start_index)

        # begin eventloop
        self._mainloop(maxloops)

    def _mainloop(self, maxloops=-1):
        """
        Args:
            maxloops (int):
                Exit after this many loops.
                Negative numbers loop infinitely.
                For testing.
        """
        try:
            while True:
                # for testing
                if maxloops == 0:
                    return False

                # render 0% progress
                self._render_progress()
                self._interpreter.eval_user_commands()

                # workers periodically die to release their memory. build as-needed
                self.manager.build_workers()

                self._evaluate_queues()
                self._evaluate_diskfull_check()

                if self.copy_finished():
                    print('Successfully Copied {} Files'.format(len(self._copyfiles)))
                    return True
                maxloops -= 1
                time.sleep(0.1)
        finally:
            self.manager.stop()
            self.manager.join(timeout=3000)

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
                data = self.started_queue.get(timeout=0)
                self._started_indexes.append(data.index)
            except queue.Empty:
                return

    def _evaluate_completed_queue(self):
        while True:
            try:
                filedata = self.completed_queue.get(timeout=0)
                self._try_remove_started_index(filedata.index)
                self._copied_indexes.append(filedata.index)
                self._render_progress(filedata=filedata)
            except queue.Empty:
                return

    def _evaluate_error_queue(self):
        while True:
            try:
                filedata = self.error_queue.get(timeout=0)
                self._try_remove_started_index(filedata.index)
                self._error_indexes.append(filedata.index)
                self._render_progress(filedata=filedata)
            except queue.Empty:
                return

    def _evaluate_diskfull_check(self):
        if self.device_full_lock.is_set():
            # request stop, wait for all workers to finish current file
            self.manager.stop()
            self.manager.join()

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
            self.reconciler.reconcile(self._copyfiles, self._copied_indexes)
            self.device_full_lock.clear()
            return 0

    def _empty_and_requeue_started_copyfiles(self):
        """
        """
        sorted_started_indexes = sorted(self._started_indexes)
        requeued = 0
        while len(self._started_indexes) > 0:
            index = sorted_started_indexes.pop(0)
            self._try_remove_started_index(index)
            self.joblist.insert(0, self._copyfiles[index])
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

            command = self.prompt.input('> ')
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

    def build_workers(self, maxloops=-1):
        """ Builds workers until number of active workers matches `options.num_workers`

        Args:
            maxloops (int, optional):
                maximum number of loops before aborting from loop.
                negative numbers are infinite.
                (param for testing).
        """
        remaining_loops = maxloops
        while True:
            if self.active_workers() < self.options.num_workers:
                worker = _MultiProcessCopierWorker(self._joblist,
                                                   self._started_queue,
                                                   self._completed_queue,
                                                   self._error_queue,
                                                   self._device_full_lock,
                                                   self.options,
                                                   maxtasks=self.options.max_worker_tasks)
                self._workers.append(worker)
                worker.start()
            else:
                break

            # exit on maxloops
            remaining_loops -= 1
            if remaining_loops == 0:
                return

    def active_workers(self):
        return len(list(filter(lambda x: x.is_alive(), self.__iter__())))

    def stop(self):
        logger.debug('Stopping Workers...')
        # worker can only process a single queue item at a time.
        # please wait afterwards.
        for i in range(self.active_workers()):
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
    def __init__(self, joblist, started_queue, completed_queue, error_queue, device_full_event, options, maxtasks=5, *args, **kwargs):
        """

        Args:
            joblist (multiprocessing.Manager.list):
                list of jobs shared between workers.
                next job at index 0.

            started_queue (multiprocessing.Queue):
                file added here when we start processing it

            completed_queue (multiprocessing.Queue):
                file added here when it is done beng processed.

            error_queue (multiprocessing.Queue):
                file added here if it could not be copied

            device_full_event (multiprocessing.Event):
                event that is set when the disk indicates it is full.

            options (copyoptions.CopyOptions):
                the copy options

            maxtasks (int):
                number of copies this process is allowed to have before it
                exits. Manager will continuously create workers as needed.
                This exists primarily to keep memory from getting fragmented
                during copies.
        """
        super(_MultiProcessCopierWorker, self).__init__(*args, **kwargs)

        self._joblist = joblist
        self._started_queue = started_queue
        self._completed_queue = completed_queue
        self._error_queue = error_queue
        self._device_full_event = device_full_event
        self.options = options

        self.maxtasks = maxtasks

    def run(self, maxloops=-1):
        """ Main loop.

        Args:
            maxloops (int, optional):
                maximum loops before loop exits.
                negative numbers loop indefinitely.
                for testing.


        Returns:
            int: number of loops ran before exit.
        """
        loop_count = 0
        files_processed = 0
        while files_processed < self.maxtasks:
            # for testing
            if maxloops - loop_count == 0:
                return loop_count

            # device lock being set also acts like a poison pill
            if self._device_full_event.is_set():
                logger.debug('Process Exit, device full')
                return loop_count

            # try retrieving next item from list, loop if unavailable
            try:
                data = self._joblist.pop(0)
            except IndexError:
                time.sleep(0.2)
                loop_count += 1
                continue

            # `None` is poison pill, causing exit
            if data is None:
                return loop_count

            # inform wip queue that job started
            self._started_queue.put(data)

            # otherwise data is a single copyfile dict.
            try:
                kwargs = dict(mtime=self.options.compare_mtime,
                              size=self.options.compare_size,
                              checksum=self.options.compare_checksum)
                if not os.path.isfile(data.dst):
                    filesystem.copyfile(src=data.src, dst=data.dst, reraise=True, log_errors=False)
                    filesystem.copyfilestat(src=data.src, dst=data.dst)
                elif filesystem.files_different(data.src, data.dst, **kwargs):
                    filesystem.copyfile(src=data.src, dst=data.dst, reraise=True, log_errors=False)
                    filesystem.copyfilestat(src=data.src, dst=data.dst)
                self._completed_queue.put(data)
            except(OSError) as exc:
                if not self._exception_indicates_device_full(exc):
                    self._error_queue.put(data)
                    raise
                self._device_full_event.set()
                return loop_count

            # increment loop count, so we can kill worker, and release memory
            files_processed += 1
            loop_count += 1

        logger.debug('Worker maxtasks reached. Exiting')
        return loop_count

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


