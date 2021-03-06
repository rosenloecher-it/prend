import locale
import logging
import traceback
import typing
from prend.config import ConfigLoader
from prend.logging_helper import LoggingHelper
from prend.rule import Rule
from prend.rule_manager import RuleManager
from prend.tools.persister import TypePersister


# pylint: disable=broad-except
class Process:

    CONFIG_SECTION_RULES = "rules"

    def __init__(self):
        self._config = None
        self._rule_manager = None
        self._exit_code = None
        self._register_rules_from_config = False

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

            TypePersister.set_storage_path(self._config.persist_dir)

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

            if self._register_rules_from_config:
                if self._config.parsed.start or self._config.parsed.toogle or \
                        self._config.parsed.foreground or self._config.parsed.ensure:
                    self._register_rules_from_config_delayed()

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

    @classmethod
    def _check_class(cls, rule):
        if not isinstance(rule, Rule):
            if rule:
                class_info = rule.__class__.__module__ + '.' + rule.__class__.__name__
            else:
                class_info = 'None'
            class_target = Rule.__module__ + '.' + Rule.__name__
            raise TypeError("{} is not of type {}!".format(class_info, class_target))

    @classmethod
    def resolve_import(cls, path: str) -> Rule.__class__:
        delimiter = path.rfind(".")
        class_name = path[delimiter + 1:len(path)]
        module_name = __import__(path[0:delimiter], globals(), locals(), [class_name])
        return getattr(module_name, class_name)

    def register_rule_instance(self, rule: Rule):
        try:
            self._check_class(rule)
            self._rule_manager.register_rule(rule)
        except Exception as ex:
            print('error: {}'.format(ex))
            self._exit_code = 1

    def register_rule_path(self, rule_instance_name: str, rule_path: str):
        try:
            rule_class = self.resolve_import(rule_path)
            rule = rule_class()
            self._check_class(rule)
            rule.set_instance_name(rule_instance_name)
            self._rule_manager.register_rule(rule)
        except Exception as ex:
            print('could not load module "{}"! {}'.format(rule_path, ex))
            self._exit_code = 1
            raise

    def register_rules_from_config(self):
        self._register_rules_from_config = True

    def _register_rules_from_config_delayed(self):
        try:
            section = self._config.rule_config.get(self.CONFIG_SECTION_RULES)
            if section is None:
                raise RuntimeError('config section "{}" not found!'.format(self.CONFIG_SECTION_RULES))

            for rule_instance_name, rule_path in section.items():
                if rule_path:
                    self.register_rule_path(rule_instance_name, rule_path)

            if self._exit_code is not None:
                raise RuntimeError('some entries could not be loaded!?')

        except Exception:
            # print('error config rules via config files: {}'.format(ex))
            raise
