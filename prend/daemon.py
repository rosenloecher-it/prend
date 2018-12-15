# Original version: https://github.com/serverdensity/python-daemon

from __future__ import print_function
import atexit
import errno
import logging
import os
import signal
import sys
import time
from prend.logging_helper import LoggingHelper


_logger = logging.getLogger(__name__)


class Daemon:
    """
    A generic daemon class.

    Usage: subclass the Daemon class and override the run() method
    """

    def __init__(self, pidfile, workdir='.', umask=0o22):
        self.pidfile = pidfile
        self.workdir = workdir
        self.umask = umask
        self.daemon_alive = True
        self.is_deamon = False

    def _do_exit(self, exit_code):
        LoggingHelper.disable_output()
        # _logger.debug('_do_exit - {}'.format(exit_code))
        sys.exit(exit_code)

    def daemonize(self):
        """
        Do the UNIX double-fork magic, see Stevens' "Advanced
        Programming in the UNIX Environment" for details (ISBN 0201563177)
        http://www.erlenstar.demon.co.uk/unix/faq_2.html#SEC16
        """
        try:
            pid = os.fork()
            if pid > 0:
                # Exit first parent
                self._do_exit(0)
            else:
                self.is_deamon = True
        except OSError as ex:
            _logger.error('fork #1 failed: %s (%s)', ex.errno, ex.strerror)
            self._do_exit(1)

        LoggingHelper.remove_logger_console_output()

        # Decouple from parent environment
        os.chdir(self.workdir)
        os.setsid()
        os.umask(self.umask)

        # Do second fork
        try:
            pid = os.fork()
            if pid > 0:
                # Exit from second parent
                self._do_exit(0)
            else:
                self.is_deamon = True
        except OSError as ex:
            _logger.error('fork #2 failed: %s (%s)', ex.errno, ex.strerror)
            self._do_exit(1)

        # noinspection PyUnusedLocal
        def sigtermhandler(signum, frame):
            self.daemon_alive = False
            _logger.info('sigtermhandler(%s)', signum)
            self.shutdown()
            self._do_exit(signum)

        signal.signal(signal.SIGTERM, sigtermhandler)
        signal.signal(signal.SIGINT, sigtermhandler)

        self.write_pidfile()

    def delete_pidfile(self):
        try:
            # the process may fork itself again
            pid_os = os.getpid()

            with open(self.pidfile, 'r') as pidhandle:
                pid_written = int(pidhandle.read().strip())
            if pid_written == pid_os:
                os.remove(self.pidfile)
        except OSError as ex:
            if ex.errno == errno.ENOENT:
                pass
            else:
                raise

    def check_pidfile_and_exit(self):
        # Check for a pidfile to see if the daemon already runs
        try:
            with open(self.pidfile, 'r') as pidhandle:
                pid = int(pidhandle.read().strip())
        except IOError:
            pid = None
        except SystemExit:
            pid = None

        if not self.exists_proc(pid):
            pid = None

        if pid:
            _logger.error('pidfile (%s) already exist. daemon is already running!? => exit', self.pidfile)
            self._do_exit(1)

    def write_pidfile(self):
        atexit.register(self.delete_pidfile)  # Make sure pid file is removed if we quit
        pid = str(os.getpid())
        # the pid has to stay open! it is closed automatically at end of daemon.
        open(self.pidfile, 'w+').write("%s\n" % pid)
        _logger.info('deamon started (pid=%s)', pid)

    def shutdown(self):
        """
        Shutdown in process - notify derived classes
        """
        pass

    def start_foreground(self):
        """
        Start as foreground process
        """
        _logger.debug('starting foreground...')

        self.check_pidfile_and_exit()
        # don't write pid, because it doesn't get deleted when aborting
        self.run()

    def start(self):
        """
        Start the daemon
        """
        _logger.debug('starting deamon...')
        self.check_pidfile_and_exit()
        self.daemonize()
        self.run()

    def stop(self):
        """
        Stop the daemon
        """
        _logger.debug('stopping...')
        pid = self.get_pid_from_file()

        if not pid:
            _logger.warning('pidfile (%s) does not exist. daemon is not running!?', self.pidfile)

            # Just to be sure. A ValueError might occur if the PID file is
            # empty but does actually exist
            if os.path.exists(self.pidfile):
                os.remove(self.pidfile)
            return  # ok, not an error in a restart

        # Try killing the daemon process
        try:
            time_sleep = 0.5
            time_wait_for_gracefully_shutdown = 5  # seconds

            time_to_wait = time_wait_for_gracefully_shutdown
            while 1:
                _logger.debug('os.kill(%s, %s)', pid, signal.SIGTERM)
                os.kill(pid, signal.SIGTERM)
                if time_to_wait < 0:  # more than x seconds
                    break
                time.sleep(time_sleep)
                time_to_wait = time_to_wait - time_sleep
                if not os.path.exists('/proc/%d' % pid):
                    break

            while 1:
                if not os.path.exists('/proc/%d' % pid):
                    break
                _logger.debug('os.kill(%s, %s)', pid, signal.SIGHUP)
                os.kill(pid, signal.SIGHUP)
                time.sleep(time_sleep)

        except OSError as ex:
            if ex.errno == errno.ESRCH:
                _logger.debug('ESRCH - no such process (%d) => OK', pid)
                if os.path.exists(self.pidfile):
                    os.remove(self.pidfile)
            else:
                raise ex

    def status(self):
        def print_func(text):
            print(text)
        self.is_running(print_func)

    def toogle(self):
        """
        toogle deamon state
        """
        if self.is_running():
            self.stop()
        else:
            self.start()

    def ensure_started(self):
        if self.is_running():
            return

        def notify_func(text):
            _logger.error(text)
        self.is_running(notify_func)  # show output
        self.start()

    def restart(self):
        """
        Restart the daemon
        """
        if self.is_running():
            self.stop()
        return self.start()

    def get_pid_from_file(self):
        try:
            with open(self.pidfile, 'r') as pidhandle:
                pid = int(pidhandle.read().strip())
        except IOError:
            pid = None
        except SystemExit:
            pid = None
        return pid

    @staticmethod
    def exists_proc(pid) -> bool:
        if pid is not None:
            if os.path.exists('/proc/{}'.format(pid)):
                return True
        return False

    def is_running(self, notify_func=None):
        pid = self.get_pid_from_file()

        if pid is None:
            if notify_func:
                notify_func('daemon is stopped')
            return False

        if self.exists_proc(pid):
            if notify_func:
                notify_func('daemon (pid={}) is running...'.format(pid))
            return True

        if notify_func:
            notify_func('daemon (pid=%s) is killed'.format(pid))
        return False

    def run(self):
        """
        You should override this method when you subclass Daemon.
        It will be called after the process has been
        daemonized by start() or restart().
        """
        raise NotImplementedError
