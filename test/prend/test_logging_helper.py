import logging
import unittest
from prend.config import Config, ConfigLoader
from prend.constants import Constants
from prend.logging_helper import LoggingHelper


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

    def test_set_explicit_module_loglevels_success(self):
        config = Config()

        logname_1 = 'app.logger_name_1'
        loglevel_1 = 'error'
        logcomp_1 = LoggingHelper.get_loglevel(loglevel_1)
        logname_2 = 'xxx.dfgdg.logger_name_1'
        loglevel_2 = 'warn'
        logcomp_2 = LoggingHelper.get_loglevel(loglevel_2)

        ConfigLoader.add_to_rule_config(config.rule_config,
                                        Constants.LOGGING,
                                        '{}|{}'.format(Constants.LOGLEVEL, logname_1),
                                        loglevel_1)
        ConfigLoader.add_to_rule_config(config.rule_config,
                                        Constants.LOGGING,
                                        '{}|{}'.format(Constants.LOGLEVEL, logname_2),
                                        loglevel_2)
        ConfigLoader.add_to_rule_config(config.rule_config,
                                        Constants.LOGGING,
                                        '{}|{}'.format(Constants.LOGLEVEL, logname_1),
                                        loglevel_1)

        LoggingHelper.set_explicit_module_loglevels(config)

        logger = logging.getLogger(logname_1)
        loglevel_out = logger.getEffectiveLevel()
        self.assertEqual(logcomp_1, loglevel_out)

        logger = logging.getLogger(logname_2)
        loglevel_out = logger.getEffectiveLevel()
        self.assertEqual(logcomp_2, loglevel_out)

    def test_set_explicit_module_loglevels_nocrash(self):
        config = Config()

        ConfigLoader.add_to_rule_config(config.rule_config,
                                        Constants.LOGGING,
                                        '{}||abc'.format(Constants.LOGLEVEL),
                                        'warn')
        ConfigLoader.add_to_rule_config(config.rule_config,
                                        Constants.LOGGING,
                                        '{}|abc'.format(Constants.LOGLEVEL),
                                        'warn')
        ConfigLoader.add_to_rule_config(config.rule_config,
                                        Constants.LOGGING,
                                        'dfasfdsafd',
                                        'warn')

        LoggingHelper.set_explicit_module_loglevels(config)

        LoggingHelper.set_explicit_module_loglevels(None)
        LoggingHelper.set_explicit_module_loglevels({})

    def test_get_logname(self):
        path = self.__module__
        name = self.__class__.__name__
        full_path = "{}.{}".format(path, name)

        ln = LoggingHelper.get_logname(self, "Xtra")
        self.assertEqual(ln, full_path + "(xtra)")

        ln = LoggingHelper.get_logname(self, name)
        self.assertEqual(ln, full_path)

        ln = LoggingHelper.get_logname(self, name.upper())
        self.assertEqual(ln, full_path)

        ln = LoggingHelper.get_logname(self, full_path)
        self.assertEqual(ln, full_path)

        ln = LoggingHelper.get_logname(self, full_path.upper())
        self.assertEqual(ln, full_path)


if __name__ == '__main__':
    unittest.main()
