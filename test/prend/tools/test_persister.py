import datetime
import os
import threading
import unittest
from prend.tools.persister import Persister, TypePersister
from test.setup_test import SetupTest
from dateutil.tz import tzoffset


class TestPersiter(unittest.TestCase):

    def test_roundtrip(self):
        work_dir = SetupTest.ensure_clean_work_dir()

        path = os.path.join(work_dir, 'persist_test.json')
        self.assertFalse(os.path.exists(path))

        p = Persister(path)

        data1 = {"abc": 123, "456": "rr", 'list': [1, 2, 3, "str"]}
        p.set_value("data1", data1)

        data2 = datetime.datetime(2018, 12, 3, 13, 7, 45, tzinfo=tzoffset(None, 3600))
        p.set_value("data2", data2)

        self.assertTrue(os.path.exists(path))

        p = Persister(path)

        comp1 = p.get_value("data1")
        self.assertEqual(comp1, None)

        comp2 = p.get_value("data2")
        self.assertEqual(comp2, None)

        p.load()

        comp1 = p.get_value("data1")
        self.assertEqual(comp1, data1)

        comp2 = p.get_datetime("data2")
        self.assertEqual(comp2, data2)

    def test_convert_datetime(self):
        d = datetime.datetime(2018, 12, 3, 13, 7, 45, tzinfo=tzoffset(None, 3600))
        c = Persister.parse_datetime(d.isoformat())
        self.assertEqual(c, d)

        d = datetime.datetime(2018, 12, 3, 13, 7, 45)
        c = Persister.parse_datetime(d.isoformat())
        self.assertEqual(c, d)

        d = datetime.datetime(2018, 12, 3, 13, 7, 45)
        c = Persister.parse_datetime('2018-12-03 13:07:45')
        self.assertEqual(c, d)

        d = datetime.datetime(2018, 12, 3, 13, 7)
        c = Persister.parse_datetime('2018-12-03 13:07')
        self.assertEqual(c, d)

        c = Persister.parse_datetime('sdfsadfsdaf')
        self.assertEqual(c, None)

        c = Persister.parse_datetime('')
        self.assertEqual(c, None)

        c = Persister.parse_datetime('  ')
        self.assertEqual(c, None)

        c = Persister.parse_datetime(123)
        self.assertEqual(c, None)

        c = Persister.parse_datetime(None)
        self.assertEqual(c, None)

    def test_convert_float(self):
        c = Persister.parse_float(1.23)
        self.assertEqual(c, 1.23)

        c = Persister.parse_float(" 1.23 ")
        self.assertEqual(c, 1.23)

        c = Persister.parse_float(" -1.23 ")
        self.assertEqual(c, -1.23)

        c = Persister.parse_float(" sdffs ")
        self.assertEqual(c, None)

        c = Persister.parse_float(None)
        self.assertEqual(c, None)

    def test_convert_int(self):
        c = Persister.parse_int(" 5 ")
        self.assertEqual(c, 5)

        c = Persister.parse_int(" -5")
        self.assertEqual(c, -5)

        c = Persister.parse_int(1.23)
        self.assertEqual(c, 1)

        c = Persister.parse_int(" 1.88 ")
        self.assertEqual(c, 2)

        c = Persister.parse_int(" -1.88 ")
        self.assertEqual(c, -2)

        c = Persister.parse_int(" sdffs ")
        self.assertEqual(c, None)

        c = Persister.parse_int(None)
        self.assertEqual(c, None)


class TestTypePersiter(unittest.TestCase):

    _lock = threading.Lock()

    def test_roundtrip(self):
        with self._lock:
            work_dir = SetupTest.ensure_clean_work_dir()

            TypePersister.set_storage_path(work_dir)
            self.assertEqual(TypePersister.get_storage_path(), work_dir)

            class_info = TypePersister.get_class_key(self)
            expected_file_path = os.path.join(work_dir, class_info + '.json')
            self.assertFalse(os.path.exists(expected_file_path))

            TypePersister.dismiss_persister(self)

            p = TypePersister.get_persister(self)
            p2 = TypePersister.get_persister(self)
            self.assertEqual(p, p2)

            data1 = datetime.datetime(2018, 12, 3, 13, 7, 45, tzinfo=tzoffset(None, 3600))
            p.set_value("data1", data1)

            self.assertTrue(os.path.exists(expected_file_path))

            TypePersister.dismiss_persister(self)

            p2 = TypePersister.get_persister(self)
            self.assertFalse(p is p2)

            comp1 = p2.get_datetime("data1")
            self.assertEqual(comp1, data1)

    def test_roundtrip_error(self):
        with self._lock:
            work_dir = SetupTest.ensure_clean_work_dir()

            TypePersister.set_storage_path(work_dir)
            self.assertEqual(TypePersister.get_storage_path(), work_dir)

            class_info = TypePersister.get_class_key(self)
            expected_file_path = os.path.join(work_dir, class_info + '.json')
            expected_bak_path = expected_file_path + '.bak'

            self.assertFalse(os.path.exists(expected_file_path))

            TypePersister.dismiss_persister(self)

            p = TypePersister.get_persister(self)

            data1 = datetime.datetime(2018, 12, 3, 13, 7, 45, tzinfo=tzoffset(None, 3600))
            p.set_value("data1", data1)

            self.assertTrue(os.path.exists(expected_file_path))

            TypePersister.dismiss_persister(self)

            os.remove(expected_file_path)
            self.assertFalse(os.path.exists(expected_file_path))
            self.assertFalse(os.path.exists(expected_bak_path))

            with open(expected_file_path, "w") as text_file:
                text_file.write("nonsense}{")

            p2 = TypePersister.get_persister(self)
            self.assertFalse(p is p2)

            comp1 = p2.get_value("data1")
            self.assertEqual(comp1, None)

            self.assertTrue(os.path.exists(expected_bak_path))
