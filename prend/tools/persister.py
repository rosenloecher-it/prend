import copy
import datetime
import json
import logging
import os
import os.path
import threading
import dateutil.parser


_logger = logging.getLogger(__name__)


class Persister:

    def __init__(self, path):
        self._data = {}
        self._lock = threading.Lock()
        self._path = path
        self._auto_save = True

    def save(self, auto_save=False):
        with self._lock:
            if not auto_save or self._auto_save:
                data_str = json.dumps(self._data, indent=4, sort_keys=True)
                with open(self._path, "w+") as text_file:
                    text_file.write(data_str)

    def set_auto_save(self, auto_save):
        with self._lock:
            self._auto_save = auto_save

    def load(self):
        with self._lock:
            with open(self._path) as text_file:
                self._data = json.load(text_file)

    def set_value(self, key: str, value):
        if isinstance(value, (datetime.datetime, datetime.date)):
            value = value.isoformat()
        else:
            value = copy.deepcopy(value)

        with self._lock:
            self._data[key] = value
        self.save(True)

    def get_value(self, key):
        clone = None
        with self._lock:
            value = self._data.get(key)
            if value:
                clone = copy.deepcopy(value)

        return clone

    def get_str(self, key):
        raw = self.get_value(key)
        return str(raw)

    def get_float(self, key):
        raw = self.get_value(key)
        return self.parse_float(raw)

    @staticmethod
    def parse_float(raw):
        if raw is None:
            return None
        try:
            return float(raw)
        except ValueError:
            return None

    def get_int(self, key):
        raw = self.get_value(key)
        return self.parse_int(raw)

    @staticmethod
    def parse_int(raw):
        if raw is None:
            return None
        try:
            return int(round(float(raw)))
        except ValueError:
            return None

    def get_datetime(self, key):
        raw = self.get_value(key)
        return self.parse_datetime(raw)

    @staticmethod
    def parse_datetime(raw):
        if raw is None:
            return None
        if not isinstance(raw, str):
            return None
        raw = raw.strip()
        if not raw:
            return None
        try:
            return dateutil.parser.parse(raw)
        except (ValueError, TypeError):
            return None

    def get_all(self):
        clone = None
        with self._lock:
            clone = copy.deepcopy(self._data)
        return clone


class TypePersister(Persister):

    _storage_path = None
    _instances = {}
    _lock_instances = threading.Lock()

    def __init__(self, path):
        super().__init__(path)

    @classmethod
    def set_storage_path(cls, path):
        with cls._lock_instances:
            if cls._storage_path is None:
                cls._storage_path = path

    @classmethod
    def get_storage_path(cls):
        with cls._lock_instances:
            return cls._storage_path

    @classmethod
    def get_class_key(cls, object_instance):
        class_info = object_instance.__class__.__module__ + '.' + object_instance.__class__.__name__
        return class_info

    @classmethod
    def get_persister(cls, object_instance):
        class_info = cls.get_class_key(object_instance)

        with cls._lock_instances:
            persister = cls._instances.get(class_info)
            if persister is not None:
                return persister

            if cls._storage_path is None:
                raise Exception("no storage path!")

            path = os.path.join(cls._storage_path, class_info + ".json")

            persister = TypePersister(path)

            if os.path.isfile(path):
                try:
                    persister.load()
                except Exception as ex:
                    _logger.error("cannot load %s! %s", path, ex)
                    cls._try_backup(path)

            try:
                persister.save()
            except Exception as ex:
                _logger.error("cannot write %s! %s", path, ex)
                raise

            cls._instances[class_info] = persister

            return persister

    @classmethod
    def dismiss_persister(cls, object_instance):
        """
        needed for test

        :param object_instance: any object instance of any type
        """
        class_info = cls.get_class_key(object_instance)
        with cls._lock_instances:
            cls._instances.pop(class_info, None)

    @classmethod
    def _try_backup(cls, path):
        try:
            if not os.path.isfile(path):
                return

            path_bak = path + ".bak"
            if os.path.isfile(path_bak):
                _logger.warning("cannot backup %s! file already exists!", path)
                return

            os.rename(path, path_bak)

        except Exception as ex:
            _logger.error("cannot backup %s => %s!\n %s", path, path_bak, ex)
