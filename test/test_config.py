import unittest
from test.setup_test import SetupTest
from prend.config import Config, ConfigLoader


class TestCliArgs(unittest.TestCase):

    def test_load_config_file(self):

        config_file = SetupTest.get_def_config_file()
        args_in = '--config {} --foreground'.format(config_file)
        # print('args_in=', args_in)
        config = ConfigLoader.parse_cli(args_in.split())
        # print('config=', config)
        self.assertTrue(config.exit_code is None)

        self.assertTrue(config.oh_rest_base_url is None)
        self.assertTrue(config.oh_username is None)
        self.assertTrue(config.oh_password is None)

        ConfigLoader.update_config_from_file(config)
        print('config={}'.format(config))
        self.assertTrue(config.exit_code is None)

        self.assertTrue(config.oh_rest_base_url is not None)
        self.assertTrue(config.loglevel is not None)
        self.assertTrue(config.logfile is not None)

    def test_parse_args(self):
        args_out = ConfigLoader.parse_cli('--config --foreground'.split())
        self.assertTrue(args_out.exit_code is not None)
        self.assertTrue(args_out.exit_code != 0)

        args_out = ConfigLoader.parse_cli('--config fileDoesNotExist.xxx --foreground'.split())
        self.assertTrue(args_out.exit_code is not None)
        self.assertTrue(args_out.exit_code != 0)

        config_file = SetupTest.get_def_config_file()
        args_in = '--config {} --foreground'.format(config_file)
        print('args_in=', args_in)
        args_out = ConfigLoader.parse_cli(args_in.split())
        print('args_out=', args_out)
        self.assertTrue(args_out.exit_code is None)

    def test_args_mode(self):

        args_out = ConfigLoader.parse_cli('-h'.split())
        self.assertTrue(args_out.parsed.help)
        self.assertTrue(args_out.exit_code == 0)
        args_out = ConfigLoader.parse_cli('--help'.split())
        self.assertTrue(args_out.parsed.help)
        self.assertTrue(args_out.exit_code == 0)
        # print('args_out:', args_out)

        args_out = ConfigLoader.parse_cli('--start'.split())
        self.assertTrue(args_out.parsed.start)

        args_out = ConfigLoader.parse_cli('--stop'.split())
        self.assertTrue(args_out.parsed.stop)

        args_out = ConfigLoader.parse_cli('--toogle'.split())
        self.assertTrue(args_out.parsed.toogle)

        args_out = ConfigLoader.parse_cli('--status'.split())
        self.assertTrue(args_out.parsed.status)

        args_out = ConfigLoader.parse_cli('--foreground'.split())
        self.assertTrue(args_out.parsed.foreground)
        args_out = ConfigLoader.parse_cli('-f'.split())
        self.assertTrue(args_out.parsed.foreground)

        args_out = ConfigLoader.parse_cli('--ensure'.split())
        self.assertTrue(args_out.parsed.ensure)
        args_out = ConfigLoader.parse_cli('-e'.split())
        self.assertTrue(args_out.parsed.ensure)

        # check no mode
        config_file = SetupTest.get_def_config_file()
        args_in = '--config {}'.format(config_file)
        print('args_in=', args_in)
        args_out = ConfigLoader.parse_cli(args_in.split())
        print('args_out=', args_out)
        self.assertTrue(args_out.exit_code is not None)

        options = ['--start', '--stop', '--toogle', '--foreground', '--status', '--ensure']

        for i in range(0, len(options) - 1):
            option1 = options[i]
            for k in range(i + 1, len(options)):
                option2 = options[k]
                print('CliArgs.evaluate([{}, {}]'.format(option1, option2))
                args_out = ConfigLoader.parse_cli([option1, option2])

                self.assertTrue(args_out.exit_code is not None)
                self.assertTrue(args_out.exit_code != 0)

    # pylint: disable=protected-access
    def test_ensure_abs_path_to_config(self):
        out = ConfigLoader._ensure_abs_path_to_config('/home/xxx/prend/prend.conf', './__test__')
        self.assertEqual('/home/xxx/prend/__test__', out)


class TestConfig(unittest.TestCase):

    def test_print(self):
        config = Config()

        # no crah
        config.print()
        config.print(True)

        config.config_file = 'test'
        config.oh_rest_base_url = 'test'
        config.oh_username = 'test'
        config.pid_file = 'test'
        config.work_dir = 'test'

        config.print()
        config.print(True)


class TestConfigLoader(unittest.TestCase):

    def test_get_app_name(self):

        app_name = ConfigLoader.get_app_name()
        print('app_name =', app_name)

        self.assertTrue(len(app_name) > 0)
        self.assertTrue(app_name.find('/') < 0)
        self.assertTrue(app_name.find('\\') < 0)

    def test_get_def_config_file(self):
        app_name = ConfigLoader.get_app_name()
        print('app_name =', app_name)

        config_file = ConfigLoader.get_def_config_file1()
        print('config_file1 =', config_file)

        config_file = ConfigLoader.get_def_config_file2()
        print('config_file2 =', config_file)


if __name__ == '__main__':
    unittest.main()

