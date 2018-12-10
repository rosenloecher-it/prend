import schedule
from abc import ABC, abstractmethod
from prend.dispatcher import Dispatcher
from prend.channel import Channel, ChannelType
from prend.oh.oh_gateway import OhGateway
from prend.state import State


class RuleException(Exception):
    pass


class Rule(ABC):

    def __init__(self):
        self._dispatcher = None
        self._oh_gateway = None

    def __repr__(self) -> str:
        return '{}()'.format(self.__class__.__name__)

    def open(self, oh_gateway: OhGateway, dispatcher: Dispatcher) -> None:
        self._dispatcher = dispatcher
        self._oh_gateway = oh_gateway
        self.register_actions()

    def is_open(self) -> bool:
        return self._dispatcher and self._oh_gateway

    def is_connected(self):
        if not self.is_open():
            return False
        return self._oh_gateway.is_connected()

    def close(self) -> None:
        pass

    def subscribe_openhab_actions(self, channel: Channel) -> None:
        self._dispatcher.register_oh_listener(channel, self)

    def subscribe_cron_actions(self, cron_key: str, job: schedule.Job) -> None:
        self._dispatcher.register_cron_listener(cron_key, job, self)

    def get_channels(self):
        states = self.get_states()
        channels = []
        for channel in states:
            channels.append(channel)
        return channels

    def get_states(self) -> dict:
        return self._oh_gateway.get_states()

    def get_state(self, channel: Channel) -> State:
        return self._oh_gateway.get_state(channel)

    def get_state_value(self, channel: Channel):
        state = self._oh_gateway.get_state(channel)
        if state:
            return state.value
        return None

    def get_item_state_value(self, channel_name: str):
        channel = Channel.create(ChannelType.ITEM, channel_name)
        state = self._oh_gateway.get_state(channel)
        if state:
            return state.value
        return None

    def send_command(self, channel: Channel, state) -> None:
        self._oh_gateway.send(True, channel, state)

    def send_update(self, channel: Channel, state) -> None:
        self._oh_gateway.send(False, channel, state)

    def send_item_command(self, channel: str, state) -> None:
        channel = Channel.create(ChannelType.ITEM, channel)
        self._oh_gateway.send(True, channel, state)

    def send_item_update(self, channel: str, state) -> None:
        channel = Channel.create(ChannelType.ITEM, channel)
        self._oh_gateway.send(False, channel, state)

    @abstractmethod
    def register_actions(self) -> None:
        """
        overwrite and register wished actions via self.register_action and self.register_schedule
        """
        pass

    @abstractmethod
    def notify_action(self, action) -> None:
        """
        overwrite and handle notifications
        :param action: notification data
        """
        pass


