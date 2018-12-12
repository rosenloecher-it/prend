from enum import Enum
from typing import Optional
import datetime
import json
from prend.channel import Channel, ChannelType
from prend.state import State, StateType


class OhEventException(Exception):
    pass


class OhIllegalEventException(OhEventException):
    def __init__(self, event):
        super().__init__('invalid event ({})!'.format(str(event) if event else 'None'))


class OhNotificationType(Enum):
    IGNORE = 0
    RELOAD = 1
    ITEM_CHANGE = 10
    ITEM_COMMAND = 11
    GROUP_CHANGE = 20
    THING_CHANGE = 30

    def __str__(self):
        return self.__repr__()

    def __repr__(self) -> str:
        return self.name

    @staticmethod
    def parse(text: Optional[str]) -> Optional['OhNotificationType']:
        # list of all events:
        # https://www.eclipse.org/smarthome/documentation/javadoc/org/eclipse/smarthome/core/events/Event.html
        result = OhNotificationType.IGNORE
        if text:
            text = text.strip()

            if text in ('ItemStateEvent', 'ItemStateChangedEvent'):
                result = OhNotificationType.ITEM_CHANGE
            elif text == 'ItemCommandEvent':
                result = OhNotificationType.ITEM_COMMAND

            elif text == 'GroupItemStateChangedEvent':
                result = OhNotificationType.GROUP_CHANGE

            elif text in ('ThingStatusInfoEvent', 'ThingStatusInfoChangedEvent'):
                result = OhNotificationType.THING_CHANGE

            elif text in ('ItemAddedEvent', 'ItemRemovedEvent', 'ItemUpdatedEvent'
                          , 'ThingAddedEvent', 'ThingRemovedEvent', 'ThingUpdatedEvent'):
                result = OhNotificationType.RELOAD
            else:
                result = OhNotificationType.IGNORE
        return result


class OhEvent:
    def __init__(self):
        self.notification_type = None
        self.channel = None
        self.state = None

    def __eq__(self, other) -> bool:
        if not other:
            return False
        if type(self) != type(other):
            return False
        if self.notification_type != other.notification_type:
            return False
        if self.channel != other.channel:
            return False
        if self.state != other.state:
            return False
        return True

    def __repr__(self) -> str:
        return '{}({}, {}, {})'.format(self.__class__.__name__, self.notification_type, self.channel, self.state)

    def is_valid(self) -> bool:
        if not self.notification_type or self.notification_type == OhNotificationType.IGNORE:
            return False

        if self.notification_type == OhNotificationType.RELOAD:
            return True

        if not self.channel:
            return False
        if not self.channel.is_valid():
            return False
        if not self.state:
            return False
        return self.state.is_valid()

    @staticmethod
    def create(notification_type: Optional[OhNotificationType], channel: Optional[Channel], state: Optional[State]):
        event = OhEvent()
        event.notification_type = notification_type
        event.channel = channel
        event.state = state
        return event

    @staticmethod
    def create_empty():
        return OhEvent()

    @staticmethod
    def extract_item_name(path: Optional[str]) -> Optional[str]:
        output = None
        if path:
            items = path.split('/')
            if len(items) == 4:
                output = items[2]
        return output

    @staticmethod
    def extract_group_name(path: Optional[str]) -> Optional[str]:
        output = None
        if path:
            items = path.split('/')
            if len(items) == 5:
                output = items[2]
        return output

    @staticmethod
    def create_from_notify_json(text: str):
        # pylint: disable=line-too-long
        # {"topic":"smarthome/items/valPvModVoltage/state","payload":"{"type":"Decimal","value":"542.20"}","type":"ItemStateEvent"}
        event = OhEvent.create_empty()
        json_data = json.loads(text)

        event.notification_type = OhNotificationType.parse(json_data.get('type'))

        if event.notification_type in [OhNotificationType.ITEM_CHANGE, OhNotificationType.ITEM_COMMAND]:
            OhEvent._fill_event_from_item(event, json_data)
        elif event.notification_type == OhNotificationType.GROUP_CHANGE:
            OhEvent._fill_event_from_group(event, json_data)
        elif event.notification_type in [OhNotificationType.THING_CHANGE]:
            OhEvent._fill_event_from_thing(event, json_data)
        elif event.notification_type in [OhNotificationType.RELOAD, OhNotificationType.IGNORE]:
            pass  # do nothing
        else:
            raise OhEventException('wrong notification type ({})!'.format(event.notification_type))

        return event

    @staticmethod
    def _fill_event_from_item(event: 'OhEvent', json_data):
        channel_type = OhEvent.get_channel_type(event.notification_type)
        channel_name = OhEvent.extract_item_name(json_data.get('topic'))
        event.channel = Channel.create(channel_type, channel_name)

        # embedded structure as string!
        payload_text = json_data.get('payload')
        if payload_text:
            payload = json.loads(payload_text)
            state_text = payload.get('type')
            state_type = payload.get('type')
            state_value = payload.get('value')
            event.state = State.convert(state_type, state_value)

    @staticmethod
    def _fill_event_from_group(event: 'OhEvent', json_data):
        channel_type = OhEvent.get_channel_type(event.notification_type)
        channel_name = OhEvent.extract_group_name(json_data.get('topic'))
        event.channel = Channel.create(channel_type, channel_name)

        # embedded structure as string!
        payload_text = json_data.get('payload')
        if payload_text:
            payload = json.loads(payload_text)
            state_type = payload.get('type')
            state_value = payload.get('value')
            event.state = State.convert(state_type, state_value)

    @staticmethod
    def _fill_event_from_thing(event: 'OhEvent', json_data):
        channel_type = OhEvent.get_channel_type(event.notification_type)
        channel_name = OhEvent.extract_item_name(json_data.get('topic'))
        event.channel = Channel.create(channel_type, channel_name)

        # embedded structure as string!
        payload_text = json_data.get('payload')
        if payload_text:
            payload = json.loads(payload_text)

            if isinstance(payload, list):
                payload_inner = payload[0]
            else:
                payload_inner = payload

            state_value = payload_inner.get('status')
            event.state = State.convert(StateType.THING_STATUS.name, state_value)

    @staticmethod
    def create_from_state_json(json_data: dict, channel_type: ChannelType):

        event = OhEvent.create_empty()

        if channel_type == ChannelType.GROUP:
            event.notification_type = OhNotificationType.GROUP_CHANGE
        else:
            event.notification_type = OhNotificationType.ITEM_CHANGE

        channel_name = json_data.get('name')
        event.channel = Channel.create(channel_type, channel_name)

        state_type = json_data.get('type')
        state_value = json_data.get('state')
        event.state = State.convert(state_type, state_value)
        return event

    @staticmethod
    def create_from_thing_json(json_data: dict):

        event = OhEvent.create_empty()

        event.notification_type = OhNotificationType.THING_CHANGE
        channel_name = json_data.get('UID')
        event.channel = Channel.create(ChannelType.THING, channel_name)

        state_value = None
        status_info = json_data.get('statusInfo')
        if status_info:
            state_value = status_info.get('status')

        event.state = State.convert(StateType.THING_STATUS.name, state_value)
        return event

    @staticmethod
    def get_channel_type(event_type: Optional[OhNotificationType]) -> Optional[ChannelType]:
        result = None
        if event_type in [OhNotificationType.ITEM_CHANGE, OhNotificationType.ITEM_COMMAND]:
            result = ChannelType.ITEM
        elif event_type in [OhNotificationType.GROUP_CHANGE, OhNotificationType.GROUP_CHANGE]:
            result = ChannelType.GROUP
        elif event_type in [OhNotificationType.THING_CHANGE, OhNotificationType.THING_CHANGE]:
            result = ChannelType.THING
        return result
