import copy
import datetime
import logging
import requests
import threading
from .oh_event import OhEvent, OhIllegalEventException, OhNotificationType
from .oh_send_data import OhSendData, OhSendFlags
from prend.action import Action
from prend.channel import Channel, ChannelType, OhIllegalChannelException
from prend.state import State
from queue import Queue, Empty
from typing import Optional


_logger = logging.getLogger(__name__)


class OhGatewayException(Exception):
    pass


class OhGatewayEventSink:
    def push_event(self, event: OhEvent) -> None:
        """overwrite for testing
        :param event:
        """
        pass


class OhGateway(OhGatewayEventSink):

    def __init__(self):
        self._cache_states_last_fetch = None
        self._cache_states_notified_reload = None
        self._channel_listeners = {}
        self._dispatcher = None
        self._last_connection_error = None
        self._lock_channel_listeners = threading.Lock()
        self._lock_state = threading.Lock()
        self._rest = None
        self._send_queue = Queue()  # synchronized
        self._states = {}

    def set_dispatcher(self, dispatcher):
        self._dispatcher = dispatcher

    def set_rest(self, rest):
        self._rest = rest

    def send_queued(self):
        something_processed = False
        start_loop = True

        send_data = None
        while send_data or start_loop:
            start_loop = False
            try:
                send_data = self._send_queue.get_nowait()
            except Empty:
                send_data = None

            if send_data:
                try:
                    self._rest.send(send_data)
                except Exception as ex:
                    _logger.error('send failed (%s: %s)!', ex.__class__.__name__, ex)
                    self._cache_states_last_fetch = None
                    self._last_connection_error = datetime.datetime.now()

        return something_processed

    def send(self, flags: OhSendFlags, channel, state):
        send_data = OhSendData(flags, channel, state)
        send_data.check()

        channel = send_data.get_channel()  # get converted channel back
        state = self.get_state(channel)
        if state is None:
            raise ValueError('no sending to not existing channels ({})!'.format(channel))

        do_send = True
        if send_data.is_flag(OhSendFlags.SEND_ONLY_IF_DIFFER):
            if not send_data.does_state_value_differ(state):
                do_send = False

        if do_send:
            self._send_queue.put(send_data)

    def get_states(self) -> dict:
        with self._lock_state:
            export = copy.deepcopy(self._states)
        return export

    # convenience function for get_states
    def get_channels(self) -> list:
        states = self.get_states()
        channels = [*states]
        return channels

    # convenience function for get_state
    def get_item_state(self, channel_name: str):
        channel = Channel.create(ChannelType.ITEM, channel_name)
        state = self.get_state(channel)
        return state

    # convenience function for get_state
    def get_item_state_value(self, channel_name: str):
        channel = Channel.create(ChannelType.ITEM, channel_name)
        state = self.get_state(channel)
        if state:
            return state.value
        return None

    def get_state(self, channel: Channel) -> Optional[State]:
        state_out = None
        if channel:
            with self._lock_state:
                state = self._states.get(channel)
                if state:
                    state_out = copy.deepcopy(state)
        return state_out

    # convenience function for get_state
    def get_state_value(self, channel: Channel):
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
                    self.push_event(event)
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

    def push_event(self, event: OhEvent) -> None:
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
                self._dispatcher.push_action(action)


