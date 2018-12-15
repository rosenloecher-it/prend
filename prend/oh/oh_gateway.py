import copy
import datetime
import logging
import requests
import threading
from prend.action import Action
from prend.channel import Channel, ChannelType, OhIllegalChannelException
from prend.oh.oh_event import OhEvent, OhIllegalEventException, OhNotificationType
from prend.state import State
from typing import Optional


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

    def __init__(self):
        self._lock_channel_listeners = threading.Lock()
        self._lock_state = threading.Lock()
        self._lock_send = threading.Lock()
        self._states = {}
        self._channel_listeners = {}
        self._dispatcher = None
        self._rest = None
        self._cache_states_notified_reload = None
        self._cache_states_last_fetch = None
        self._last_connection_error = None

    def set_dispatcher(self, dispatcher):
        self._dispatcher = dispatcher

    def set_rest(self, rest):
        self._rest = rest

    def send(self, send_command: bool, channel: Channel, state):
        if not isinstance(send_command, bool):
            raise TypeError()
        if not isinstance(channel, Channel):
            raise TypeError()
        # if not isinstance(state, State):
        #     raise TypeError()

        with self._lock_send:
            try:
                self._rest.send(send_command, channel, state)
            except Exception as ex:
                _logger.error('send failed (%s: %s)!', ex.__class__.__name__, ex)
                self._cache_states_last_fetch = None
                self._last_connection_error = datetime.datetime.now()
                raise

    # convenience funtion for send
    def send_command(self, channel: Channel, state) -> None:
        self.send(True, channel, state)

    # convenience funtion for send
    def send_update(self, channel: Channel, state) -> None:
        self.send(False, channel, state)

    # convenience funtion for send
    def send_item_command(self, channel_name: str, state) -> None:
        channel = Channel.create(ChannelType.ITEM, channel_name)
        self.send(True, channel, state)

    # convenience funtion for send
    def send_item_update(self, channel_name: str, state) -> None:
        channel = Channel.create(ChannelType.ITEM, channel_name)
        self.send(False, channel, state)

    def get_states(self):
        with self._lock_state:
            export = copy.deepcopy(self._states)
        return export

    # convenience funtion for get_states
    def get_channels(self):
        states = self.get_states()
        channels = []
        for channel in states:
            channels.append(channel)
        return channels

    def get_state(self, channel: Channel) -> Optional[State]:
        state_out = None
        if channel:
            with self._lock_state:
                state = self._states.get(channel)
                if state:
                    state_out = copy.deepcopy(state)
        return state_out

    # convenience funtion for get_state
    def get_item_state(self, channel_name: str):
        channel = Channel.create(ChannelType.ITEM, channel_name)
        state = self.get_state(channel)
        return state

    # convenience funtion for get_state
    def get_state_value(self, channel: Channel):
        state = self.get_state(channel)
        if state:
            return state.value
        return None

    # convenience funtion for get_state
    def get_item_state_value(self, channel_name: str):
        channel = Channel.create(ChannelType.ITEM, channel_name)
        state = self.get_state(channel)
        if state:
            return state.value
        return None

    def is_connected(self):
        if not self._rest:
            return False
        if not self._cache_states_last_fetch:
            return False
        if self._last_connection_error:
            return False
        return True

    def get_last_cache_time(self):
        return self._cache_states_last_fetch

    def cache_states(self):
        try:
            if self._rest:
                time_start = datetime.datetime.now()
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
                _logger.debug('item cache loaded (%fs)', (self._cache_states_last_fetch - time_start).total_seconds())

        except Exception as ex:
            _logger.error('cache_states failed (%s: %s)!', ex.__class__.__name__, ex)
            if not isinstance(ex, requests.exceptions.RequestException):
                _logger.exception(ex)
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


