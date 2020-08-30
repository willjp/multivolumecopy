from multivolumecopy.copiers import multiprocesscopier
from multivolumecopy import copyoptions, copyfile
from multivolumecopy.resolvers import resolver
from multivolumecopy.reconcilers import reconciler
import multiprocessing
import pytest
import mock


class MockResolver(resolver.Resolver):
    """ Fake Resolver that returns copyfiles without using disk.
    """
    FILE_A = copyfile.CopyFile(src='/src/a/1.txt', dst='/dst/a/1.txt', relpath='a/1.txt', bytes=1024, index=0)
    FILE_B = copyfile.CopyFile(src='/src/a/2.txt', dst='/dst/a/2.txt', relpath='a/2.txt', bytes=1024, index=1)
    FILE_C = copyfile.CopyFile(src='/src/a/3.txt', dst='/dst/a/3.txt', relpath='a/4.txt', bytes=1024, index=2)
    def get_copyfiles(self, device_startindex=None, start_index=None):
        return tuple([self.FILE_A, self.FILE_B, self.FILE_C])


class MockReconciler(reconciler.Reconciler):
    """ Fake Reconciler that does not delete anything.
    """
    def calculate(self, copyfiles, copied_indexes):
        return set()


class TestMultiProcessCopier:
    def setup(self):
        # don't resolve/reconcile using real files,
        # and do not start any worker processes
        self.options = copyoptions.CopyOptions()
        self.resolver = MockResolver(self.options)
        self.reconciler = MockReconciler(self.resolver, self.options)
        self.copier = multiprocesscopier.MultiProcessCopier(self.resolver,
                                                            self.options,
                                                            self.reconciler)
        self.copier.manager = mock.Mock()
        self.copier.prompt = mock.Mock()
        self.options.output = '/dst'

    def test_copy_finished_returns_false_when_copyfiles_remain(self):
        """ No files have been copied, so job is not complete.
        """
        self.copier.start(device_start_index=0, start_index=0, maxloops=1)
        assert self.copier.copy_finished() is False

    def test_copy_finished_returns_true_when_all_copyfiles_completed(self):
        self.copier.completed_queue.put(MockResolver.FILE_A)
        self.copier.completed_queue.put(MockResolver.FILE_B)
        self.copier.completed_queue.put(MockResolver.FILE_C)
        self.copier.start(device_start_index=0, start_index=0, maxloops=1)
        assert self.copier.copy_finished() is True

    def test_copy_finished_returns_true_when_all_copyfiles_errored(self):
        self.copier.error_queue.put(MockResolver.FILE_A)
        self.copier.error_queue.put(MockResolver.FILE_B)
        self.copier.error_queue.put(MockResolver.FILE_C)
        self.copier.start(device_start_index=0, start_index=0, maxloops=1)
        assert self.copier.copy_finished() is True

    def test_copy_finished_returns_true_when_sum_of_copied_files_and_errors_equals_total_files(self):
        self.copier.completed_queue.put(MockResolver.FILE_A)
        self.copier.error_queue.put(MockResolver.FILE_B)
        self.copier.error_queue.put(MockResolver.FILE_C)
        self.copier.start(device_start_index=0, start_index=0, maxloops=1)
        assert self.copier.copy_finished() is True

    def test_prompt_diskfull_prompts_when_diskfull_and_job_not_finished(self):
        with pytest.raises(SystemExit):
            self.copier.device_full_lock.set()
            # force quit instead of looping forever or continuing copy
            self.copier.prompt.input.return_value = 'q'
            self.copier.start(device_start_index=0, start_index=0, maxloops=1)
            self.copier.prompt.assert_called_with('> ')

    def test_prompt_diskfull_does_not_prompt_if_diskfull_but_job_finished(self):
        self.copier.device_full_lock.set()
        self.copier.completed_queue.put(MockResolver.FILE_A)
        self.copier.completed_queue.put(MockResolver.FILE_B)
        self.copier.completed_queue.put(MockResolver.FILE_C)
        # if test condition is not met, we do not want to wait in endless loop
        self.copier.prompt.input.return_value = 'q'
        self.copier.start(device_start_index=0, start_index=0, maxloops=1)

    def test_requeues_started_copyfiles_when_diskfull(self):
        with pytest.raises(SystemExit):
            self.copier.device_full_lock.set()
            self.copier.completed_queue.put(MockResolver.FILE_A)
            self.copier.started_queue.put(MockResolver.FILE_B)
            self.copier.started_queue.put(MockResolver.FILE_C)
            # force quit instead of looping forever or continuing copy
            self.copier.prompt.input.return_value = 'q'
            self.copier.start(device_start_index=0, start_index=0, maxloops=1)

        # items are taken from index-0 first, so order is inverted
        assert self.copier.joblist[0] == MockResolver.FILE_C
        assert self.copier.joblist[1] == MockResolver.FILE_B


class Test_MultiProcessCopierWorkerManager:
    def setup(self):
        self.joblist = [MockResolver.FILE_A]
        self.started_queue = multiprocessing.Queue()
        self.completed_queue = multiprocessing.Queue()
        self.error_queue = multiprocessing.Queue()
        self.device_full_lock = multiprocessing.Lock()
        self.options = copyoptions.CopyOptions()
        self.options.output = '/dst'
        self.options.num_workers = 3
        self.manager = multiprocesscopier._MultiProcessCopierWorkerManager(
            self.joblist,
            self.started_queue,
            self.completed_queue,
            self.error_queue,
            self.device_full_lock,
            self.options
        )

    @mock.patch('multivolumecopy.copiers.multiprocesscopier._MultiProcessCopierWorker')
    def test_build_workers_creates_workers_when_none(self, m_worker):
        # num_workers + 1 -- we want to confirm stops at correct number of workers
        self.manager.build_workers(maxloops=4)
        self.manager.active_workers() == 3

    def test_build_workers_creates_extra_workers_as_required(self):
        """ In our pool of 3x workers, 2x are not active.
        They should be restarted.
        """
        self.manager._workers = [mock.Mock(), mock.Mock(), mock.Mock()]
        self.manager._workers[1].is_alive.return_value = False
        self.manager._workers[2].is_alive.return_value = False

        self.manager.build_workers(maxloops=2)
        self.manager.active_workers() == 3

    def test_iter_removes_and_closes_exited_workers(self):
        """ __iter__ cleans up references to old workers.
        """
        worker_a = mock.Mock()
        worker_b = mock.Mock()
        worker_c = mock.Mock()

        worker_b.is_alive.return_value = False
        worker_c.is_alive.return_value = False

        self.manager._workers = [worker_a, worker_b, worker_c]

        for worker in self.manager:
            pass
        assert len(self.manager._workers) == 1

    def test_stop_issues_poison_pill_to_all_active_workers(self):
        worker_a = mock.Mock()
        worker_b = mock.Mock()
        self.manager._workers = [worker_a, worker_b]
        self.manager.stop()
        assert self.joblist[:2] == [None, None]

    def test_terminate_terminates_processes(self):
        worker_a = mock.Mock()
        worker_b = mock.Mock()
        self.manager._workers = [worker_a, worker_b]
        self.manager.terminate()
        assert worker_a.terminate.called
        assert worker_b.terminate.called

    def test_terminate_only_terminates_active_processes(self):
        worker_a = mock.Mock()
        worker_b = mock.Mock()
        worker_b.is_alive.return_value = False

        self.manager._workers = [worker_a, worker_b]
        self.manager.terminate()
        assert worker_a.terminate.called
        assert not worker_b.terminate.called

    def test_join_joins_workers(self):
        worker_a = mock.Mock()
        worker_b = mock.Mock()

        self.manager._workers = [worker_a, worker_b]
        self.manager.join()
        assert worker_a.join.called
        assert worker_b.join.called

    def test_join_skips_inactive_workers(self):
        worker_a = mock.Mock()
        worker_b = mock.Mock()
        worker_b.is_alive.return_value = False

        self.manager._workers = [worker_a, worker_b]
        self.manager.join()
        assert worker_a.join.called
        assert not worker_b.join.called


class Test_MultiProcessCopierWorker:
    def setup(self):
        self.joblist = [MockResolver.FILE_A]
        self.started_queue = multiprocessing.Queue()
        self.completed_queue = multiprocessing.Queue()
        self.error_queue = multiprocessing.Queue()
        self.device_full_lock = multiprocessing.Event()
        self.options = copyoptions.CopyOptions()
        self.options.output = '/dst'
        self.worker = multiprocesscopier._MultiProcessCopierWorker(
            self.joblist,
            self.started_queue,
            self.completed_queue,
            self.error_queue,
            self.device_full_lock,
            maxtasks=3,
        )

    @mock.patch('multivolumecopy.copiers.multiprocesscopier.filesystem')
    def test_exits_if_device_full(self, m_filesystem):
        self.device_full_lock.set()
        loops = self.worker.run(maxloops=3)
        assert loops == 0

    @mock.patch('multivolumecopy.copiers.multiprocesscopier.filesystem')
    def test_loops_while_list_empty(self, m_filesystem):
        # first iteration will process file A,
        self.worker._joblist = [MockResolver.FILE_A]
        self.worker.maxtasks = 5
        loops = self.worker.run(maxloops=3)
        assert loops == 3

    @mock.patch('multivolumecopy.copiers.multiprocesscopier.filesystem')
    def test_poison_pill_kills_process(self, m_filesystem):
        self.worker._joblist = [None]
        loops = self.worker.run(maxloops=3)
        assert loops == 0

    @mock.patch('multivolumecopy.copiers.multiprocesscopier.filesystem')
    def test_copies_file(self, m_filesystem):
        filedata = MockResolver.FILE_A
        self.worker._joblist = [filedata]
        loops = self.worker.run(maxloops=1)
        m_filesystem.copyfile.assert_called_with(
            src=filedata.src,
            dst=filedata.dst,
            reraise=True,
            log_errors=False
        )

    @mock.patch('multivolumecopy.copiers.multiprocesscopier.filesystem')
    def test_copies_file_stats(self, m_filesystem):
        filedata = MockResolver.FILE_A
        self.worker._joblist = [filedata]
        loops = self.worker.run(maxloops=1)
        m_filesystem.copyfile.assert_called_with(
            src=filedata.src,
            dst=filedata.dst,
            reraise=True,
            log_errors=False
        )

    @mock.patch('multivolumecopy.copiers.multiprocesscopier.filesystem')
    def test_worker_stops_at_maxtasks(self, m_filesystem):
        self.worker._joblist = [MockResolver.FILE_A, MockResolver.FILE_B, MockResolver.FILE_C]
        self.worker.maxtasks = 2
        loops = self.worker.run(maxloops=5)
        assert loops == 2


