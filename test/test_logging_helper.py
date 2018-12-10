import logging
import unittest
from prend.logging_helper import LoggingHelper
from prend.config import Config


class TestLoggingHelper(unittest.TestCase):

    def test_init(self):
        config = Config()
        # dir should not exist
        config.logfile = '/asdfasd/cxvasvcsd/cvsadfvsafv/kjhgjhg.log'

        # no crash
        LoggingHelper.init(config)

    def test_get_loglevel(self):
        loglevel_default = LoggingHelper.LOGLEVEL_DEFAULT

        self.assertEqual(loglevel_default, LoggingHelper.get_loglevel(None))
        self.assertEqual(loglevel_default, LoggingHelper.get_loglevel(''))

        self.assertEqual(logging.DEBUG, LoggingHelper.get_loglevel('debug'))

        self.assertEqual(logging.WARN, LoggingHelper.get_loglevel('WARN'))
        self.assertEqual(logging.WARN, LoggingHelper.get_loglevel(' warNing'))

        self.assertEqual(logging.ERROR, LoggingHelper.get_loglevel(' error'))
        self.assertEqual(logging.ERROR, LoggingHelper.get_loglevel(' ERR '))
        self.assertEqual(logging.CRITICAL, LoggingHelper.get_loglevel(' critial'))
        self.assertEqual(logging.CRITICAL, LoggingHelper.get_loglevel(' crit '))
        self.assertEqual(logging.CRITICAL, LoggingHelper.get_loglevel(' FATAL '))

    def test_remove_logger_console_output(self):
        LoggingHelper.remove_logger_console_output()

    def test_disable_other_loggers(self):
        # no crash
        LoggingHelper.disable_other_loggers()
        LoggingHelper.disable_other_loggers()

    #
    # @classmethod
    # def get_loglevel(cls, loglevel_in):
    #     loglevel_def = logging.INFO
    #
    #     if not loglevel_in:
    #         return loglevel_def
    #
    #     loglevel_in = loglevel_in.strip().lower()
    #     if loglevel_in == 'info':
    #         return logging.INFO
    #     elif loglevel_in == 'debug':
    #         return logging.
    #     elif loglevel_in.index('warn') == 0:
    #         return logging.WARN
    #     elif loglevel_in.index('err') == 0:
    #         return logging.ERROR
    #     elif loglevel_in.index('crit') == 0 or loglevel_in == 'fatal':
    #         return logging.CRITICAL
    #     return loglevel_def


