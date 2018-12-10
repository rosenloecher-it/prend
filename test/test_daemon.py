import unittest
import os
from prend.daemon import Daemon
from test.setup_test import SetupTest


class TestBaseDaemon(Daemon):  # don't call it TestDaemon

    def __init__(self, config):
        super().__init__(config.pid_file, config.work_dir)
        self.exit_code = None

    def _do_exit(self, exit_code):
        self.exit_code = exit_code

    def daemonize(self):
        pass  # do nothing

    def run(self):
        pass  # do nothing


class TestDaemon(unittest.TestCase):

    def test_pid_handling(self):
        config = SetupTest.get_config()
        daemon = TestBaseDaemon(config)

        if os.path.exists(config.pid_file):
            os.remove(config.pid_file)

        self.assertTrue(not os.path.isfile(config.pid_file))
        daemon.write_pidfile()
        self.assertTrue(os.path.isfile(config.pid_file))
        daemon.write_pidfile()

        self.assertTrue(daemon.exit_code is None)
        daemon.check_pidfile_and_exit()
        self.assertTrue(daemon.exit_code is not None)
        daemon.exit_code = None

        self.assertTrue(daemon.is_running())

        written_pid = daemon.get_pid()
        self.assertEqual(written_pid, os.getpid())

        daemon.delete_pidfile()
        self.assertTrue(not os.path.isfile(config.pid_file))

