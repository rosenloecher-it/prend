import logging

import schedule
from abc import ABC, abstractmethod

from prend.action import Action
from prend.channel import Channel
from prend.dispatcher import Dispatcher
from prend.logging_helper import LoggingHelper
from prend.oh.oh_gateway import OhGateway
from prend.oh.oh_send_data import OhSendFlags
from prend.state import State
from prend.tools.convert import Convert
from typing import Optional


class RuleException(Exception):
    pass


class Rule(ABC):

    def __init__(self):
        self._dispatcher = None  # type: Dispatcher
        self._oh_gateway = None  # type: OhGateway
        self._config = None
        self._instance_name = None
        self._logger = None

    def __repr__(self) -> str:
        if not self._instance_name or self.__class__.__name__.lower() == self._instance_name.lower():
            return self.__class__.__name__
        else:
            return '{}({})'.format(self.__class__.__name__, self._instance_name)

    def _get_logger(self):
        if self._logger is None:
            log_name = LoggingHelper.get_logname(self, self._instance_name)
            self._logger = logging.getLogger(log_name)
        return self._logger

    def set_instance_name(self, instance_name: str):
        if not self._instance_name:
            self._instance_name = instance_name

    def get_instance_name(self):
        return self._instance_name

    def set_config(self, config):
        self._config = config

    def set_dispatcher(self, dispatcher):
        self._dispatcher = dispatcher

    def set_oh_gateway(self, oh_gateway):
        self._oh_gateway = oh_gateway

    def open(self) -> None:
        self.register_actions()

    def is_open(self) -> bool:
        return self._dispatcher and self._oh_gateway

    def is_connected(self):
        if not self.is_open():
            return False
        return self._oh_gateway.is_connected()

    def close(self) -> None:
        pass

    def subscribe_channel_actions(self, channel: Channel) -> None:
        self._dispatcher.register_oh_listener(channel, self)

    def subscribe_cron_actions(self, cron_key: str, job: schedule.Job) -> None:
        self._dispatcher.register_cron_listener(cron_key, job, self)

    def get_config(self, section_name: str, value_name: str, fallback: Optional[str] = None):
        section = self._config.get(section_name)
        if not section:
            return fallback
        value = section.get(value_name)
        if value is None:
            return fallback
        return value

    def get_config_bool(self, section_name: str, value_name: str, fallback: Optional[bool] = None):
        value_str = self.get_config(section_name, value_name, None)
        value = Convert.convert_to_bool(value_str, fallback)
        return value

    def get_config_int(self, section_name: str, value_name: str, fallback: Optional[int] = None):
        value_str = self.get_config(section_name, value_name, None)
        value = Convert.convert_to_int(value_str, fallback)
        return value

    def get_config_float(self, section_name: str, value_name: str, fallback: Optional[float] = None):
        value_str = self.get_config(section_name, value_name, None)
        value = Convert.convert_to_float(value_str, fallback)
        return value

    def get_channels(self) -> list:
        return self._oh_gateway.get_channels()

    def get_states(self) -> dict:
        return self._oh_gateway.get_states()

    # convenience function for get_state
    def get_item_state(self, channel_name: str) -> State:
        return self._oh_gateway.get_item_state(channel_name)

    # convenience function for get_state
    def get_item_state_value(self, channel_name: str):
        return self._oh_gateway.get_item_state_value(channel_name)

    def get_state(self, channel: Channel) -> State:
        return self._oh_gateway.get_state(channel)

    # convenience function for get_state
    def get_state_value(self, channel: Channel):
        return self._oh_gateway.get_state_value(channel)

    def send(self, flags: OhSendFlags, channel, state):
        self._oh_gateway.send(flags, channel, state)

    @abstractmethod
    def register_actions(self) -> None:
        """
        overwrite and register wished actions via self.register_action and self.register_schedule
        """
        pass

    @abstractmethod
    def notify_action(self, action: Action) -> None:
        """
        overwrite and handle notifications
        :param action: notification data
        """
        pass
