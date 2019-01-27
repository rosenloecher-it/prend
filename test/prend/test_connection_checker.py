import datetime
import unittest
from prend.connection_checker import ConnectionChecker
from prend.constants import Constants


class MockConCheOhObserver:

    def __init__(self):
        self._is_connected = True

    def is_connected(self):
        return self._is_connected


class MockConCheOhGateway:

    def __init__(self):
        self._is_connected = True
        self._last_cache_time = None

    def is_connected(self):
        return self._is_connected

    def get_last_cache_time(self):
        return self._last_cache_time


class MockConnectionChecker(ConnectionChecker):

    def __init__(self):
        super().__init__()
        self._current_time = None

    def get_current_time(self):
        return self._current_time


class TestConnectionChecker(unittest.TestCase):

    def setUp(self):
        self.gateway = MockConCheOhGateway()
        self.observer = MockConCheOhObserver()

        self.con_check = MockConnectionChecker()
        self.con_check.set_oh_gateway(self.gateway)
        self.con_check.set_observer(self.observer)

    def test_no_gateway(self):
        try:
            self.con_check.set_oh_gateway(None)
            self.con_check.check_connection_state()
            self.assertTrue(False)
        except Exception:
            self.assertTrue(True)

    def test_no_observer(self):
        try:
            self.con_check.set_oh_gateway(None)
            self.con_check.check_connection_state()
            self.assertTrue(False)
        except Exception:
            self.assertTrue(True)

    def test_reconnect_observer(self):

        # all good
        self.observer._is_connected = True
        self.con_check._current_time = datetime.datetime.now()

        self.con_check.check_connection_state()
        out = self.con_check.should_reconnect_observer()
        self.assertEqual(False, out)

        # observer disconnects
        self.observer._is_connected = False
        self.con_check._current_time = datetime.datetime.now()

        self.con_check.check_connection_state()
        out = self.con_check.should_reconnect_observer()
        self.assertEqual(False, out)  # no reload immediatly

        # wait!
        self.observer._is_connected = False
        offset_seconds = Constants.WAIT_AFTER_CONNECTION_ERROR_SEC / 2
        self.con_check._current_time = self.con_check._current_time + datetime.timedelta(seconds=offset_seconds)

        self.con_check.check_connection_state()
        out = self.con_check.should_reconnect_observer()
        self.assertEqual(False, out)  # no reload immediatly

        # run now
        self.observer._is_connected = False
        offset_seconds = Constants.WAIT_AFTER_CONNECTION_ERROR_SEC  # go over wait time
        self.con_check._current_time = self.con_check._current_time + datetime.timedelta(seconds=offset_seconds)

        self.con_check.check_connection_state()
        out = self.con_check.should_reconnect_observer()
        self.assertEqual(True, out)  # no reload immediatly

        # do it again => reseted state
        self.con_check.check_connection_state()
        out = self.con_check.should_reconnect_observer()
        self.assertEqual(False, out)

    def test_reconnect_gateway(self):

        # newer cached but connected
        self.con_check._current_time = datetime.datetime.now()
        self.gateway._is_connected = True
        offset_seconds = -1 * Constants.WAIT_FORCE_FULL_RELOAD_SEC / 2

        self.con_check.check_connection_state()
        out = self.con_check.should_reconnect_oh_gateway()
        self.assertEqual(True, out)

        # all good
        self.con_check._current_time = datetime.datetime.now()
        self.gateway._is_connected = True
        offset_seconds = -1 * Constants.WAIT_FORCE_FULL_RELOAD_SEC / 2
        self.gateway._last_cache_time = self.con_check._current_time + datetime.timedelta(seconds=offset_seconds)

        self.con_check.check_connection_state()
        out = self.con_check.should_reconnect_oh_gateway()
        self.assertEqual(False, out)

        # cache outdated
        offset_seconds = Constants.WAIT_FORCE_FULL_RELOAD_SEC
        self.con_check._current_time = self.con_check._current_time + datetime.timedelta(seconds=offset_seconds)

        self.con_check.check_connection_state()
        out = self.con_check.should_reconnect_oh_gateway()
        self.assertEqual(True, out)

        # simulate cache_states
        self.gateway._last_cache_time = self.con_check._current_time

        # check again
        offset_seconds = Constants.WAIT_FORCE_FULL_RELOAD_SEC / 2
        self.con_check._current_time = self.con_check._current_time + datetime.timedelta(seconds=offset_seconds)

        self.con_check.check_connection_state()
        out = self.con_check.should_reconnect_oh_gateway()
        self.assertEqual(False, out)

        # disconnect
        self.gateway._is_connected = False
        self.con_check.check_connection_state()
        out = self.con_check.should_reconnect_oh_gateway()
        self.assertEqual(False, out)

        # reconnect again
        offset_seconds = Constants.WAIT_FORCE_FULL_RELOAD_SEC
        self.con_check._current_time = self.con_check._current_time + datetime.timedelta(seconds=offset_seconds)

        self.gateway._is_connected = False
        self.con_check.check_connection_state()
        out = self.con_check.should_reconnect_oh_gateway()
        self.assertEqual(True, out)


if __name__ == '__main__':
    unittest.main()

