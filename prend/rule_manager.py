import time
import datetime
import logging
from .action import Action
from .connection_checker import ConnectionChecker
from .daemon import Daemon
from .dispatcher import Dispatcher
from .oh.oh_gateway import OhGateway
from .oh.oh_observer import OhObserver
from .oh.oh_rest import OhRest


# https://github.com/serverdensity/python-daemon


_logger = logging.getLogger(__name__)


class RuleManagerException(Exception):
    pass


class RuleManager(Daemon):
    def __init__(self, config):
        super().__init__(pidfile=config.pid_file, workdir=config.work_dir)

        self._config = config
        self._rules = []
        self._dispatcher = Dispatcher()
        self._rest = OhRest(config)
        self._oh_gateway = OhGateway()
        self._oh_gateway.set_dispatcher(self._dispatcher)
        self._oh_gateway.set_rest(self._rest)
        self._observer = None
        self._con_checker = ConnectionChecker()
        self._con_checker.set_oh_gateway(self._oh_gateway)

        self.last_status_log = None
        self.last_check_connection = None
        self.time_usage_dispatch = 0
        self.time_usage_state = 0
        self.time_usage_sleep = 0
        self.time_usage_send = 0
        self.time_usage_start = None

    def status(self):
        super().status()
        self._config.print(True)

    def register_rule(self, rule):
        if rule:
            self._rules.append(rule)

    def check_start_conditions(self) -> None:
        if not self._rules:
            raise RuleManagerException('no app registered - nothing to do!')

    def shutdown_observer(self):
        try:
            if self._observer:
                self._observer.shutdown()
                self._observer = None
        except Exception as ex:
            _logger.exception(ex)

    def shutdown_rules(self):
        try:
            for rule in self._rules:
                try:
                    _logger.debug('rule.close(%s)', rule)
                    rule.close()
                except Exception as ex:
                    _logger.exception(ex)
            self._rules.clear()
        # pylint: disable=broad-except
        except Exception as ex:
            _logger.exception(ex)

    def shutdown_rest(self):
        try:
            if self._rest:
                self._oh_gateway.send_queued()
                self._rest.close()
                self._rest = None
        except Exception as ex:
            _logger.exception(ex)

    def shutdown(self):
        _logger.info('shutdown')

        self.shutdown_observer()
        self.shutdown_rules()
        self.shutdown_rest()

        super().shutdown()

    def _restart_observer(self):
        _logger.debug('_restart_observer')
        if self._observer:
            self.shutdown_observer()
        self._observer = OhObserver(self._config, self._oh_gateway)
        self._observer.start()
        self._con_checker.set_observer(self._observer)

    def _open_rules(self):
        for rule in self._rules:
            rule.set_config(self._config.rule_config)
            rule.set_dispatcher(self._dispatcher)
            rule.set_oh_gateway(self._oh_gateway)
            rule.open()

        startup_action = Action.create_startup_action()
        self._dispatcher.push_action(startup_action)

    def start_foreground(self):
        """
        Start as foreground process
        """
        _logger.debug('starting foreground...')

        self.check_pidfile_and_exit()
        # don't write pid, because it doesn't get deleted when aborting
        self.loop_events()

    def run(self):
        self.loop_events()

    def loop_events(self):

        try:
            self._rest.open()
            self._restart_observer()
            self._oh_gateway.cache_states()

            self._open_rules()

            self.last_check_connection = datetime.datetime.now()
            self.last_status_log = datetime.datetime.now()

            self._reset_time_usage()

            while True:
                something_processed = False

                if self._run_check_connection():
                    something_processed = True

                if self._run_dispatch():
                    something_processed = True

                if self._run_send():
                    something_processed = True

                self._run_status_log()

                if not something_processed:
                    sleep_time = 0.03
                    time.sleep(sleep_time)
                    self.time_usage_sleep += sleep_time

        except KeyboardInterrupt:
            _logger.debug('KeyboardInterrupt')
        except Exception as ex:
            _logger.exception(ex)
        finally:
            self.shutdown()

    def print_channels(self):
        """
        Prints all openhab channels
        """

        try:
            print('print openhab channels')

            self._rules = []  # don't process any rule

            self._rest.open()
            self._oh_gateway.cache_states()

            lines = []

            states = self._oh_gateway.get_states()  # don't lock all time

            for channel, state in states.items():
                line = "{}: {}".format(channel, state)
                lines.append(line)

            lines.sort()

            for line in lines:
                print(line)

        except Exception as ex:
            _logger.exception(ex)
        finally:
            self.shutdown()

    def _reset_time_usage(self):
        self.time_usage_dispatch = 0
        self.time_usage_state = 0
        self.time_usage_sleep = 0
        self.time_usage_send = 0
        self.time_usage_start = datetime.datetime.now()

    def _run_check_connection(self):
        wait_check_connection_sec = 3

        something_processed = False
        # check observer if running
        diff = datetime.datetime.now() - self.last_check_connection
        if diff.seconds >= wait_check_connection_sec:
            time_temp = datetime.datetime.now()
            self.last_check_connection = datetime.datetime.now()

            self._con_checker.check_connection_state()
            if self._con_checker.should_reconnect_observer():
                self._restart_observer()
                something_processed = True
            if self._con_checker.should_reconnect_oh_gateway():
                self._oh_gateway.cache_states()
                something_processed = True

            self.time_usage_state += (datetime.datetime.now() - time_temp).total_seconds()

        return something_processed

    def _run_dispatch(self):
        something_processed = False
        time_temp = datetime.datetime.now()
        if self._dispatcher.dispatch():
            something_processed = True
        self.time_usage_dispatch += (datetime.datetime.now() - time_temp).total_seconds()
        return something_processed

    def _run_send(self):
        something_processed = False
        time_temp = datetime.datetime.now()
        if self._oh_gateway.send_queued():
            something_processed = True
        self.time_usage_send += (datetime.datetime.now() - time_temp).total_seconds()
        return something_processed

    def _run_status_log(self):
        wait_status_log_sec = 600

        diff = datetime.datetime.now() - self.last_status_log
        if diff.seconds >= wait_status_log_sec:
            self.last_status_log = datetime.datetime.now()

            sum_all = (datetime.datetime.now() - self.time_usage_start).total_seconds()
            time_coverage = 100.0 * (self.time_usage_dispatch + self.time_usage_state +
                                     self.time_usage_sleep + self.time_usage_send) / sum_all
            share_dispatch = 100.0 * self.time_usage_dispatch / sum_all
            share_send = 100.0 * self.time_usage_send / sum_all
            share_sleep = 100.0 * self.time_usage_sleep / sum_all

            _logger.info('alive + time shares: cov=%.1f%%, send=%.1f%%, dispatch=%.1f%%, sleep=%.1f%%',
                         time_coverage, share_send, share_dispatch, share_sleep)

            self._reset_time_usage()
