import argparse
import configparser
import os
import sys
from prend.constants import Constants
from prend.tools.convert import Convert


# https://docs.python.org/3/library/argparse.html


class CliParser(argparse.ArgumentParser):

    def __init__(self):
        super().__init__(
            description=Constants.APP_DESC,
            add_help=False
        )
        self.exit_code = None

    def exit(self, status=0, message=None):
        """
        overwritten base function to avoid app exits => unit testing possible!
        """
        if message:
            print(message)
        self.exit_code = status

    @classmethod
    def create_parser(cls):
        """
        delivers configures/read-to-use cli arg parser

        """
        parser = CliParser()

        parser.add_argument(
            '--config', '-c',
            # type=argparse.FileType('r'),
            help='config file (search {}, {})'.format(ConfigLoader.get_def_config_file1(),
                                                      ConfigLoader.get_def_config_file2())
        )
        parser.add_argument(
            '--foreground', '-f',
            action='store_true',
            help='mode: start as foreground process'
        )
        parser.add_argument(
            '--start',
            action='store_true',
            help='mode: start deamon'
        )
        parser.add_argument(
            '--stop',
            action='store_true',
            help='mode: stop deamon'
        )
        parser.add_argument(
            '--status',
            action='store_true',
            help='mode: show deamon status'
        )
        parser.add_argument(
            '--ensure', '-e',
            action='store_true',
            help='mode: ensures that the daemon is running, start if necessary'
        )
        parser.add_argument(
            '--toogle',
            action='store_true',
            help='mode: toogle deamon'
        )
        parser.add_argument(
            '--print_channels', '-p',
            action='store_true',
            help='mode: print currently loaded openhab channels with states and exit'
        )
        parser.add_argument(
            '--help', '-h',
            action='store_true',
            help='show this help message and exit'
        )
        parser.add_argument(
            '--version', '-v',
            action='version',
            version='{} v{}'.format(ConfigLoader.get_app_name(), Constants.APP_VERSION)
        )

        return parser


class Config:
    """
    data structure to hold all config data
    """
    def __init__(self):
        self.config_file = None
        self.exit_code = None
        self.locale = None
        self.logfile = None
        self.loglevel = None
        self.log_config_file = None
        self.oh_password = None
        self.oh_rest_base_url = None
        self.oh_username = None
        self.oh_simulate_sending = False
        self.parsed = None
        self.pid_file = None
        self.work_dir = None
        self.timeout = None
        self.rule_config = {}

    def __repr__(self) -> str:
        t = '{}(exit={}; conffile={}; rest={}; log={}:{}; parsed=<{}>)'
        return t.format(self.__class__.__name__, self.exit_code, self.config_file, self.oh_rest_base_url,
                        self.loglevel, self.logfile, self.parsed)

    def print(self, print_all=False):
        lines = []

        if self.config_file or print_all:
            lines.append('config file   = {}'.format(self.config_file))
        if self.oh_rest_base_url or print_all:
            lines.append('oh rest url   = {}'.format(self.oh_rest_base_url))
        if self.oh_username or print_all:
            lines.append('username      = {}'.format(self.oh_username))
        if self.oh_simulate_sending or print_all:
            lines.append('simulate send = {}'.format(self.oh_simulate_sending))
        if self.pid_file or print_all:
            lines.append('pid file      = {}'.format(self.pid_file))
        if self.work_dir or print_all:
            lines.append('work dir      = {}'.format(self.work_dir))
        if self.log_config_file or print_all:
            lines.append('log conf file = {}'.format(self.log_config_file))
        if self.logfile or print_all:
            lines.append('log file      = {}'.format(self.logfile))

        if len(lines) > 0:
            print('\nconfiguration:')
            for line in lines:
                print(line)
            print('')


class ConfigLoader:

    @classmethod
    def get_def_config_file1(cls):
        """
        determine path and name of default config file
        """
        main = os.path.abspath(sys.modules['__main__'].__file__)
        dirname = os.path.dirname(main)
        config_file = os.path.join(dirname, '{}{}'.format(cls.get_app_name(), Constants.CONFIG_EXT))
        return config_file

    @classmethod
    def get_def_config_file2(cls):
        """
        sesach in /etc/<app_name>
        """
        config_file = os.path.join('/etc', '{}{}'.format(cls.get_app_name(), Constants.CONFIG_EXT))
        return config_file

    @classmethod
    def get_app_name(cls):
        """
        determine app name based on main script name
        """
        main = os.path.abspath(sys.modules['__main__'].__file__)
        basename = os.path.basename(main)
        app_name, ext_not_needed = os.path.splitext(basename)
        return app_name

    @classmethod
    def parse_cli(cls, cli_args=None):
        """
        evaluate cli args and loads the config file
        :param cli_args: <None> = default paras from command line; <grgs string list> for testing
        :return: "Config" data structure
        """
        parser = CliParser.create_parser()

        config = Config()

        try:
            if cli_args:
                config.parsed = parser.parse_args(cli_args)
            else:
                config.parsed = parser.parse_args()

            config.exit_code = parser.exit_code

            # print('config.parsed', config.parsed)

            if config.parsed.help:  # even == 0
                parser.print_help()
                config.exit_code = 0
                return config

            if config.exit_code is not None:
                return config

            cls._check_modes(config)

            search_config_files = [cls.get_def_config_file1(), cls.get_def_config_file2()]
            if config.parsed.config:
                config.config_file = config.parsed.config
            else:
                for found_config_file in search_config_files:
                    if os.path.isfile(found_config_file):
                        config.config_file = found_config_file
                        break

            if not config.config_file or not os.path.isfile(config.config_file):
                raise FileNotFoundError('error: could not find any config file! ({})'.format(search_config_files))

        except Exception as ex:
            if ex:
                print('error: {}'.format(ex))
            config.exit_code = 2

        return config

    @classmethod
    def _read_from_config_parser(cls, parser, section, key):
        try:
            data = parser[section].get(key, fallback=None)
            return data
        except KeyError:
            return None

    @classmethod
    def _read_bool_config_parser(cls, parser, section, key, default_value) -> bool:
        text = cls._read_from_config_parser(parser, section, key)
        data = Convert.convert_to_bool(text, default_value)
        return data

    @staticmethod
    def add_to_rule_config(ruleconf, section_name, value_name, value):
        section = ruleconf.get(section_name)
        if not section:
            section = {}
            ruleconf[section_name] = section
        section[value_name] = value

    @classmethod
    def update_config_from_file(cls, config, init_app_do_not_raise=False):

        if not os.path.isfile(config.config_file):
            if init_app_do_not_raise:
                config.exit_code = 3
                print('error: config file ({}) not found!'.format(config.config_file))
                return
            raise FileNotFoundError('error: config file ({}) does not exist!'.format(config.config_file))

        try:
            file_reader = configparser.ConfigParser()
            file_reader.read(config.config_file)

            section_logging = Constants.LOGGING
            config.logfile = cls._read_from_config_parser(file_reader, section_logging, 'logfile')
            config.loglevel = cls._read_from_config_parser(file_reader, section_logging, 'loglevel')
            config.log_config_file = cls._read_from_config_parser(file_reader, section_logging, 'log_config_file')
            config.log_delete_at_start = \
                cls._read_bool_config_parser(file_reader, section_logging, 'delete_at_start', False)

            section_openhab = 'openhab'
            config.oh_rest_base_url = cls._read_from_config_parser(file_reader, section_openhab, 'rest_base_url')
            config.oh_username = cls._read_from_config_parser(file_reader, section_openhab, 'username')
            config.oh_password = cls._read_from_config_parser(file_reader, section_openhab, 'password')
            config.oh_simulate_sending = \
                cls._read_bool_config_parser(file_reader, section_openhab, 'simulate_sending', False)

            section_system = 'system'
            config.locale = cls._read_from_config_parser(file_reader, section_system, 'locale')
            config.pid_file = cls._read_from_config_parser(file_reader, section_system, 'pid_file')
            config.work_dir = cls._read_from_config_parser(file_reader, section_system, 'work_dir')

            app_name = cls.get_app_name()

            if not config.loglevel:
                config.loglevel = 'info'

            if not config.logfile:
                config.logfile = '/var/log/{}.log'.format(app_name)
            else:
                config.logfile = cls._ensure_abs_path_to_config(config.config_file, config.logfile)

            if config.log_config_file:
                config.log_config_file = cls._ensure_abs_path_to_config(config.config_file, config.log_config_file)
                if not os.path.isfile(config.log_config_file):
                    raise FileNotFoundError('error: "log_config_file" not exists! ({})'.format(config.log_config_file))

            if not config.work_dir:
                config.work_dir = '/var/lib/{}'.format(app_name)
            else:
                config.work_dir = cls._ensure_abs_path_to_config(config.config_file, config.work_dir)

            if not config.pid_file:
                config.pid_file = '/var/run/{}.pid'.format(app_name)
            else:
                config.pid_file = cls._ensure_abs_path_to_config(config.config_file, config.pid_file)

            if not os.path.isdir(config.work_dir):
                raise FileNotFoundError('error: work dir does not exists! ({})'.format(config.work_dir))

            config.rule_config = {s: dict(file_reader.items(s)) for s in file_reader.sections()}
            cls.add_to_rule_config(config.rule_config, section_logging, 'log_config_file', config.log_config_file)
            cls.add_to_rule_config(config.rule_config, section_logging, 'logfile', config.logfile)
            cls.add_to_rule_config(config.rule_config, section_logging, 'loglevel', config.loglevel)
            cls.add_to_rule_config(config.rule_config, section_openhab, 'simulate_sending', config.oh_simulate_sending)
            cls.add_to_rule_config(config.rule_config, section_system, 'config_file', config.config_file)
            cls.add_to_rule_config(config.rule_config, section_system, 'locale', config.locale)
            cls.add_to_rule_config(config.rule_config, section_system, 'pid_file', config.pid_file)
            cls.add_to_rule_config(config.rule_config, section_system, 'work_dir', config.work_dir)

        except Exception as ex:
            if init_app_do_not_raise:
                print('error: {}'.format(ex))
                config.exit_code = 1
            else:
                raise

    @classmethod
    def _ensure_abs_path_to_config(cls, config_file, path_in):
        if not os.path.isabs(path_in):
            dirname = os.path.dirname(config_file)
            path_out = os.path.realpath(os.path.join(dirname, path_in))
            return path_out
        return path_in

    @classmethod
    def update_log_config(cls):
        # todo implement
        pass

    @classmethod
    def _check_modes(cls, config):
        # return True in case of error
        counter = 0
        if config.parsed:
            if config.parsed.start:
                counter += 1
            if config.parsed.stop:
                counter += 1
            if config.parsed.toogle:
                counter += 1
            if config.parsed.status:
                counter += 1
            if config.parsed.foreground:
                counter += 1
            if config.parsed.ensure:
                counter += 1
            if config.parsed.print_channels:
                counter += 1

        if counter > 1:
            print('\nerror: use only 1 mode!')
            config.exit_code = 2
        elif counter == 0:
            print('\nerror: missing mode!')
            config.exit_code = 2
