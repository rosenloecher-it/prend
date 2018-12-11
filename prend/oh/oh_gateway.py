from typing import Optional
import copy
import threading
import logging
import datetime
from prend.action import Action
from prend.constants import Constants
from prend.channel import Channel, OhIllegalChannelException
from prend.oh.oh_event import OhEvent, OhIllegalEventException, OhNotificationType
from prend.state import State


_logger = logging.getLogger(__name__)


class OhGatewayException(Exception):
    pass


class OhGatewayEventSink:
    def queue_event(self, event: OhEvent) -> None:
        """overwrite for testing
        :param event:
        """
        pass


class OhGateway(OhGatewayEventSink):
    TIME_WAIT_ANOTHER_RELOAD_SEC = 15
    TIME_WAIT_LAST_RELOAD_SEC = 60

    def __init__(self, dispatcher, rest):
        self._lock_state = threading.Lock()
        self._states = {}
        self._lock_channel_listeners = threading.Lock()
        self._channel_listeners = {}
        self._dispatcher = dispatcher
        self._rest = rest
        self._cache_states_notified_reload = None
        self._cache_states_last_fetch = None
        self._last_connection_error = None
        self._rest = rest

    def send(self, send_command: bool, channel: Channel, state):
        try:
            self._rest.send(send_command, channel, state)
        except Exception as ex:
            _logger.error('send failed (%s: %s)!', ex.__class__.__name__, ex)
            self._cache_states_last_fetch = None
            self._last_connection_error = datetime.datetime.now()
            raise

    def get_states(self):
        with self._lock_state:
            export = copy.deepcopy(self._states)
        return export

    def get_state(self, channel: Channel) -> Optional[State]:
        state_out = None
        if channel:
            with self._lock_state:
                state = self._states.get(channel)
                if state:
                    state_out = copy.deepcopy(state)
        return state_out

    def is_connected(self):
        return self._cache_states_last_fetch and not self._last_connection_error

    def get_last_connection_error(self):
        return self._last_connection_error

    def reset_cache_status(self):
        self._cache_states_last_fetch = None

    def cache_states_if_needed(self):
        do_reload = False
        while True:

            if self._last_connection_error:
                diff_error = (datetime.datetime.now() - self._last_connection_error).total_seconds()
                if diff_error < Constants.WAIT_AFTER_CONNECTION_ERROR_SEC:
                    break
            if not self._cache_states_last_fetch:
                do_reload = True
                break
            diff_force = (datetime.datetime.now() - self._cache_states_last_fetch).total_seconds()
            if diff_force > Constants.WAIT_FORCE_FULL_RELOAD_SEC:
                do_reload = True
                break
            if not self._cache_states_notified_reload:
                break  # no notification
            diff_note = (datetime.datetime.now() - self._cache_states_notified_reload).total_seconds()
            if diff_note < self.TIME_WAIT_ANOTHER_RELOAD_SEC:
                break
            diff_last = (datetime.datetime.now() - self._cache_states_last_fetch).total_seconds()
            if diff_last < self.TIME_WAIT_LAST_RELOAD_SEC:
                break
            do_reload = True
            break

        if do_reload:
            self.cache_states()
        return do_reload

    def cache_states(self):
        try:
            if self._rest:
                existing_channels = {}
                events = self._rest.fetch_all()
                for event in events:
                    self.queue_event(event)
                    existing_channels[event.channel] = event.state

                all_states = self.get_states()  # don't lock all time
                for channel in all_states:
                    existing_state = existing_channels.get(channel)
                    if not existing_state:
                        with self._lock_state:
                            del self._states[channel]

                self._cache_states_notified_reload = None
                self._last_connection_error = None
                self._cache_states_last_fetch = datetime.datetime.now()
                _logger.debug('item cache loaded')
        except Exception as ex:
            _logger.error('_cache_states failed (%s: %s)!', ex.__class__.__name__, ex)
            self._cache_states_last_fetch = None
            self._last_connection_error = datetime.datetime.now()

    def _import_newer_state(self, channel: Channel, state_new: State) -> bool:
        if not channel or not channel.is_valid():
            raise OhIllegalChannelException(channel)
        with self._lock_state:
            state = self._states.get(channel)
            if state:
                changed = state.import_newer_state(state_new)
            else:
                state_clone = copy.deepcopy(state_new)
                self._states[channel] = state_clone
                changed = True

        # _logger.debug('queue _import_newer_state: %s | %s', channel, changed)
        return changed

    def queue_event(self, event: OhEvent) -> None:
        if not event or not event.is_valid():
            raise OhIllegalEventException(event)
        # _logger.debug('queue event: %s', event)

        if event.notification_type == OhNotificationType.RELOAD:
            self._cache_states_notified_reload = datetime.datetime.now()
        else:
            action = Action.create_from_event(event)
            action.state_old = self.get_state(action.channel)  # copied action

            self._import_newer_state(action.channel, action.state_new)

            if action.should_be_published():
                self._dispatcher.queue_action(action)


