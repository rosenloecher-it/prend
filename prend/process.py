import locale
import logging
import traceback
import typing
from prend.config import ConfigLoader
from prend.logging_helper import LoggingHelper


# pylint: disable=broad-except
class Process:
    _config = None
    _rule_manager = None
    _exit_code = None

    def _print_and_return(self, exit_code):
        if self._config:
            self._config.print()
        return exit_code

    def init(self):
        try:
            self._config = ConfigLoader.parse_cli()
            if self._config.exit_code is not None:
                return self._print_and_return(self._config.exit_code)
            ConfigLoader.update_config_from_file(self._config, init_app_do_not_raise=True)
            if self._config.exit_code is not None:
                return self._print_and_return(self._config.exit_code)

            self._config.exit_code = LoggingHelper.init(self._config)
            if self._config.exit_code is not None:
                return self._print_and_return(self._config.exit_code)

            LoggingHelper.set_explicit_module_loglevels(self._config)

            from prend.rule_manager import RuleManager
            self._rule_manager = RuleManager(self._config)

            self._init_locale(self._config.locale)

            return None

        except Exception as ex:
            print('error: {}'.format(ex))
            print(traceback.format_exc())
            return 1

    @staticmethod
    def _init_locale(locale_name: typing.Optional[str]):
        try:
            if locale_name:
                locale_name = locale_name.strip()
                locale.setlocale(locale.LC_ALL, locale_name)
            return True
        except locale.Error as ex:
            print('set locale failed (use e.g. "de_DE.UTF8", not "{}"): {}'.format(locale_name, ex))
        return False

    def run(self):
        logger = logging.getLogger(__name__)
        LoggingHelper.disable_other_loggers()

        try:
            if self._exit_code is not None:
                return self._exit_code
            if not self._config or not self._rule_manager:
                return 1

            if self._config.parsed.stop:
                logger.debug('run(stop)')
                self._rule_manager.stop()
            elif self._config.parsed.start:
                logger.debug('run(start)')
                self._rule_manager.start()
            elif self._config.parsed.toogle:
                logger.debug('run(toggle)')
                self._rule_manager.toogle()
            elif self._config.parsed.status:
                logger.debug('run(status)')
                self._rule_manager.status()
            elif self._config.parsed.foreground:
                logger.debug('run(foreground)')
                self._rule_manager.start_foreground()
            elif self._config.parsed.ensure:
                logger.debug('run(ensure)')
                self._rule_manager.ensure_started()
            elif self._config.parsed.print_channels:
                logger.debug('run(print channels)')
                self._rule_manager.print_channels()

            return 0
        except Exception as ex:
            print('error: {}'.format(ex))
            print(traceback.format_exc())
            return 1

    def register_rule(self, rule):
        try:
            self._rule_manager.register_rule(rule)
        except Exception as ex:
            print('error: {}'.format(ex))
            self._exit_code = 1
