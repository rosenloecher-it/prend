import datetime
from prend.constants import Constants


class ConnectionChecker:

    def __init__(self, oh_gateway=None):
        self._observer = None
        self._oh_gateway = oh_gateway

        self._reconnect_observer = False
        self._reconnect_observer_after = None

        self._reconnect_oh_gateway = False
        self._reconnect_oh_gateway_after = None

        self._time_reconnection = Constants.WAIT_AFTER_CONNECTION_ERROR_SEC
        self._time_reload_gateway_cache = Constants.WAIT_FORCE_FULL_RELOAD_SEC

    def set_observer(self, observer):
        self._observer = observer

    def set_oh_gateway(self, oh_gateway):
        self._oh_gateway = oh_gateway

    # noinspection PyMethodMayBeStatic
    def _time_now(self):
        # overwrite for tests
        return datetime.datetime.now()

    def check_connection_state(self):
        """tasks
        - slow down reconnects if connection errors
        - if observer gets disconnected => reconnect gateway too
        - gateway: eload cache after some time
        """
        if not self._observer or not self._oh_gateway:
            raise ValueError()

        self._reconnect_observer = False
        self._reconnect_oh_gateway = False

        paralyse_gateway_connection = False
        time_now = self._time_now()

        # check observer
        if self._observer.is_connected():
            # nothing to do
            self._reconnect_observer = False
            self._reconnect_observer_after = None

        else:

            # likely connection error => force reload
            if not self._reconnect_observer_after:
                self._reconnect_observer = False  # not yet
                self._reconnect_observer_after = time_now + datetime.timedelta(seconds=self._time_reconnection)
                # do also reset gateway connection
                paralyse_gateway_connection = True
            else:
                if self._reconnect_observer_after < time_now:
                    self._reconnect_observer = True
                    # let: self._reconnect_observer_after
                else:
                    self._reconnect_observer = False  # not yet + wait

        # check gateway
        if self._oh_gateway.is_connected() and not paralyse_gateway_connection:
            self._reconnect_oh_gateway_after = None
            last_cache_time = self._oh_gateway.get_last_cache_time() or (time_now - datetime.timedelta(days=1))
            if last_cache_time < (time_now - datetime.timedelta(seconds=self._time_reload_gateway_cache)):
                self._reconnect_oh_gateway = True
            else:
                self._reconnect_oh_gateway = False

        else:
            if not self._reconnect_oh_gateway_after:
                self._reconnect_oh_gateway = False  # not yet
                self._reconnect_oh_gateway_after = time_now + datetime.timedelta(seconds=self._time_reconnection)
            else:
                if self._reconnect_oh_gateway_after < time_now:
                    self._reconnect_oh_gateway = True
                    # let: self._reconnect_oh_gateway_after
                else:
                    self._reconnect_oh_gateway = False  # not yet + wait

        if self._reconnect_oh_gateway_after and self._reconnect_observer_after:
            if self._reconnect_oh_gateway_after < self._reconnect_observer_after:
                self._reconnect_oh_gateway_after = self._reconnect_observer_after

    def should_reconnect_observer(self) -> bool:
        if self._reconnect_observer:
            self._reconnect_observer_after = None
        return self._reconnect_observer

    def should_reconnect_oh_gateway(self) -> bool:
        if self._reconnect_oh_gateway:
            self._reconnect_oh_gateway_after = None
        return self._reconnect_oh_gateway

