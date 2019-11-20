import os
import pathlib
from prend.config import ConfigLoader
from prend.constants import Constants


class SetupTestException(Exception):
    pass


class SetupTest:

    # region folded: work dir
    @classmethod
    def get_work_dir(cls):
        project_dir = cls.get_project_dir()
        out = os.path.join(project_dir, '__test__')
        return out

    @classmethod
    def ensure_work_dir(cls):
        work_dir = cls.get_work_dir()
        exists = os.path.exists(work_dir)
        is_dir = os.path.isdir(work_dir)

        if exists and not is_dir:
            raise NotADirectoryError(work_dir)
        if not exists:
            os.makedirs(work_dir)

        return work_dir

    @classmethod
    def ensure_clean_work_dir(cls):
        work_dir = cls.get_work_dir()
        exists = os.path.exists(work_dir)
        # is_dir = os.path.isdir(work_dir)

        if not exists:
            cls.ensure_work_dir()
        else:
            cls.clean_dir_recursively(work_dir)

        return work_dir

    # endregion

    @classmethod
    def clean_dir_recursively(cls, path_in):
        dirobj = pathlib.Path(path_in)
        if not dirobj.is_dir():
            return
        for item in dirobj.iterdir():
            if item.is_dir():
                cls.clean_dir_recursively(item)
                os.rmdir(item)
            else:
                item.unlink()

    @classmethod
    def get_def_config_file(cls):
        project_dir = cls.get_project_dir()
        config_file = os.path.join(project_dir, '{}{}'.format('tests', Constants.CONFIG_EXT))
        if not os.path.isfile(config_file):
            print('error: config file ({}) has to be created!'.format(config_file))
            raise FileNotFoundError('error: config file ({}) does not exist!'.format(config_file))
        return config_file

    @classmethod
    def get_project_dir(cls):
        file_path = os.path.dirname(__file__)
        # go up one time
        out = os.path.dirname(file_path)
        return out

    @classmethod
    def get_config(cls):
        config_file = SetupTest.get_def_config_file()
        args_in = '--config {} --foreground'.format(config_file)
        config = ConfigLoader.parse_cli(args_in.split())
        if config.exit_code is not None:
            raise SetupTestException()
        ConfigLoader.update_config_from_file(config)
        if config.exit_code is not None:
            raise SetupTestException()
        config.work_dir = cls.get_work_dir()
        config.logfile = os.path.join(config.work_dir, 'test.log')
        config.loglevel = 'debug'
        config.oh_rest_base_url = 'dummy_url'
        return config
