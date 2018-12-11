import time
import datetime
import logging
from prend.oh.oh_observer import OhObserver
from prend.oh.oh_rest import OhRest
from prend.daemon import Daemon
from prend.oh.oh_gateway import OhGateway
from .dispatcher import Dispatcher


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
        self._oh_gateway = OhGateway(self._dispatcher, self._rest)
        self._observer = None

    def status(self):
        super().status()
        self._config.print(True)

    def register_rule(self, rule):
        if rule:
            self._rules.append(rule)

    def check_start_conditions(self) -> None:
        if not self._rules:
            raise RuleManagerException('no prend_app registered - nothing to do!')

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
        except Exception as ex:
            _logger.exception(ex)

    def shutdown_rest(self):
        try:
            if self._rest:
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

    def _check_and_start_observer(self):
        do_create = False
        if self._observer:
            if not self._observer.is_alive():
                do_create = True
                self.shutdown_observer()
                if self._oh_gateway:
                    self._oh_gateway.reset_cache_status()  # likely connection error => force reload
        else:
            do_create = True
        if do_create:
            self._observer = OhObserver(self._config, self._oh_gateway)
            self._observer.start()

    def open_rules(self):
        for rule in self._rules:
            rule.set_config(self._config.rule_config)
            rule.set_dispatcher(self._dispatcher)
            rule.set_oh_gateway(self._oh_gateway)
            rule.open()

    def run(self):

        try:
            self._check_and_start_observer()
            self._rest.open()
            self.open_rules()

            wait_check_observer_sec = 10
            last_check_observer = datetime.datetime.now()

            wait_alive_message_sec = 60
            last_alive_message = datetime.datetime.now()

            while True:
                something_processed = False

                # check observer if running
                diff = datetime.datetime.now() - last_check_observer
                if diff.seconds >= wait_check_observer_sec:
                    last_check_observer = datetime.datetime.now()
                    self._check_and_start_observer()

                if self._oh_gateway.cache_states_if_needed():
                    something_processed = True

                if self._dispatcher.dispatch():
                    something_processed = True

                diff = datetime.datetime.now() - last_alive_message
                if diff.seconds >= wait_alive_message_sec:
                    last_alive_message = datetime.datetime.now()
                    _logger.debug('alive')

                if not something_processed:
                    time.sleep(0.03)

        except KeyboardInterrupt:
            _logger.debug('KeyboardInterrupt')
        except Exception as ex:
            _logger.exception(ex)
        finally:
            self.shutdown()



