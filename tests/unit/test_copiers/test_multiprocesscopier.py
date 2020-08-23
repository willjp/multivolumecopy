from multivolumecopy.copiers import multiprocesscopier
from multivolumecopy import copyoptions



class TestMultiProcessCopier:
    def test_start_build_workers(self):
        assert False

    def test_start_rebuilds_workers_as_required(self):
        assert False

    def test_started_items_recorded(self):
        assert False

    def test_error_indexes_recorded(self):
        assert False

    def test_copy_finished_returns_false_when_copyfiles_remain(self):
        assert False

    def test_copy_finished_returns_true_when_all_copyfiles_completed(self):
        assert False

    def test_copy_finished_returns_true_when_sum_of_copied_files_and_errors_equals_total_files(self):
        assert False

    def test_full_disk_prompts_user_for_input(self):
        assert False


class Test_MultiProcessCopierWorkerManager:
    def test_build_workers_creates_workers_when_none(self):
        assert False

    def test_build_workers_creates_extra_workers_as_required(self):
        assert False

    def test_active_workers_works(self):
        assert False

    def test_stop_queue_poison_pill(self):
        pass

    def test_terminate_terminates_processes(self):
        pass

    def test_join_without_timeout(self):
        pass

    def test_join_with_timeout(self):
        pass


class Test_MultiProcessCopierWorker:
    def test_exits_if_device_full(self):
        assert False

    def test_loops_while_list_empty(self):
        assert False

    def test_poison_pill_kills_process(self):
        assert False

    def test_copies_file(self):
        assert False

    def test_worker_stops_at_maxtasks(self):
        assert False


