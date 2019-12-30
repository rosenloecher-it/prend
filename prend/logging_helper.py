import logging
import logging.config
import logging.handlers
import os
import sys
from prend.constants import Constants


"""
multiprocessing_logging
    https://stackoverflow.com/questions/641420/how-should-i-log-while-using-multiprocessing-in-python
    https://github.com/jruere/multiprocessing-logging
"""


class LoggingHelper:
    LOGLEVEL_DEFAULT = logging.INFO

    @classmethod
    def init(cls, config):
        import multiprocessing_logging
        multiprocessing_logging.install_mp_handler()

        if config.log_config_file:
            defaults = None
            if config.logfile:
                defaults = {'default_logfile': config.logfile}
                if config.log_delete_at_start:
                    if os.path.isfile(config.logfile):
                        os.remove(config.logfile)

            logging.config.fileConfig(config.log_config_file, defaults=defaults, disable_existing_loggers=False)

        elif config.logfile:
            try:
                dirname = os.path.dirname(config.logfile)
                if not os.path.isdir(dirname):
                    print('error: cannot write log file ({}). dir does not exist!'.format(config.logfile))
                    return 1

                if config.log_delete_at_start:
                    if os.path.isfile(config.logfile):
                        os.remove(config.logfile)

                logging.basicConfig(
                    format='%(asctime)s [%(levelname)8s] <%(process)5d> %(name)s: %(message)s',
                    level=cls.get_loglevel(config.loglevel),
                    handlers=[
                        logging.handlers.RotatingFileHandler(config.logfile, maxBytes=1048576, backupCount=20),
                        logging.StreamHandler(sys.stdout)
                    ]
                )
            except Exception as ex:
                print('error - init logging failed -', ex)
                return 1
        return None

    @classmethod
    def get_loglevel(cls, loglevel_in):
        loglevel_def = logging.INFO

        if not loglevel_in:
            return loglevel_def

        loglevel_in = loglevel_in.strip().lower()
        if loglevel_in == 'info':
            return logging.INFO
        if loglevel_in == 'debug':
            return logging.DEBUG
        if loglevel_in.startswith('warn'):
            return logging.WARN
        if loglevel_in.startswith('err'):
            return logging.ERROR
        if loglevel_in.startswith('crit') or loglevel_in == 'fatal':
            return logging.CRITICAL
        return loglevel_def

    @classmethod
    def set_explicit_module_loglevels(cls, config):
        try:
            if config is None:
                return
            if not hasattr(config, 'rule_config'):
                return
            if config.rule_config is None:
                return
            section = config.rule_config.get(Constants.LOGGING)
            if section is None:
                return

            search_for = '{}|'.format(Constants.LOGLEVEL)
            for config_item in section:
                if not config_item.startswith(search_for):
                    continue
                parts = config_item.split('|')
                if len(parts) != 2:
                    continue
                value = section.get(config_item)
                if not value:
                    continue
                loglevel = cls.get_loglevel(value)
                logger_name = parts[1]
                if len(logger_name) < 1:
                    continue
                logger = logging.getLogger(logger_name)
                if not logger:
                    continue
                logger.setLevel(loglevel)

        except Exception as ex:
            logger = logging.getLogger(__name__)
            if logger:
                logger.exception(ex)
            else:
                print('set_explicit_module_loglevels failed: %s'.format(ex))

    @staticmethod
    def remove_logger_console_output():
        # StreamHandler was added to log to console (additional to file)
        # (for debugging in foreground mode, but not useful within a deamon)
        root_logger = logging.getLogger()
        for handler in root_logger.handlers:
            if type(handler) is logging.StreamHandler:
                root_logger.removeHandler(handler)
                break

    @staticmethod
    def disable_other_loggers():
        logger_temp = logging.getLogger("schedule")
        if logger_temp:
            logger_temp.setLevel(logging.WARNING)
        logger_temp = logging.getLogger("urllib3.connectionpool")
        if logger_temp:
            logger_temp.setLevel(logging.WARNING)
        logger_temp = logging.getLogger("asyncio")
        if logger_temp:
            logger_temp.setLevel(logging.WARNING)

    @staticmethod
    def disable_output():
        sys.stdout = os.devnull
        sys.stderr = os.devnull

    @classmethod
    def get_logname(cls, instance_class, instance_name):

        class_path = instance_class.__module__
        class_name = instance_class.__class__.__name__
        class_full = "{}.{}".format(class_path, class_name)

        # logname ist used for config handling, which ist all lower case
        if instance_name:
            instance_name = instance_name.lower()

        if instance_name and instance_name != class_name.lower() and instance_name != class_full.lower():
            log_name = "{}.{}({})".format(class_path, instance_class.__class__.__name__, instance_name)
        else:
            log_name = class_full
        return log_name
