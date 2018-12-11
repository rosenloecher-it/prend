import logging
import logging.handlers
import os
import sys


class LoggingHelper:
    LOGLEVEL_DEFAULT = logging.INFO

    _inited = False

    @classmethod
    def init(cls, config):
        import multiprocessing_logging
        multiprocessing_logging.install_mp_handler()

        if config.logfile:
            cls._inited = True

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
                        logging.handlers.RotatingFileHandler(config.logfile, maxBytes=(1048576 * 10), backupCount=5),
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

    # @classmethod
    # def update_level(cls, config):
    #     root_logger = logging.getLogger()
    #     if root_logger:
    #         root_logger.setLevel(config.loglevel)

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
