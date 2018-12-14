from enum import Enum
import typing


class OhIllegalChannelException(Exception):
    def __init__(self, channel):
        super().__init__('invalid channel ({})!'.format(str(channel) if channel else 'None'))


class ChannelType(Enum):
    STARTUP = 1
    CRON = 2
    ITEM = 3
    GROUP = 4
    THING = 5

    def __str__(self):
        return self.__repr__()

    def __repr__(self) -> str:
        return self.name

    @staticmethod
    def parse(text) -> typing.Optional['ChannelType']:
        result = None

        if text:
            text = text.strip().upper()
            for en in ChannelType:
                if en.name == text:
                    result = en
                    break

        return result


class Channel:
    def __init__(self) -> None:
        self.type = None
        self.name = None

    def __eq__(self, other) -> bool:
        if not other:
            return False
        if type(self) != type(other):
            return False
        if self.type != other.type:
            return False

        if self.type == ChannelType.STARTUP and self.type == other.type:
            return True  # no name check neccessary

        if self.name != other.name:
            return False
        return True

    def __hash__(self):
        return hash((self.type, self.name))

    def __repr__(self) -> str:
        return '{}({},{})'.format(self.__class__.__name__, self.type, self.name)

    def is_valid(self) -> bool:
        if not self.type:
            return False
        if not self.name:
            return False
        return True

    @staticmethod
    def create(channel_type: ChannelType, name: str) -> 'Channel':
        channel = Channel()
        channel.type = channel_type
        channel.name = name
        return channel

    @staticmethod
    def create_item(name: str) -> 'Channel':
        channel = Channel()
        channel.type = ChannelType.ITEM
        channel.name = name
        return channel

    @staticmethod
    def create_startup() -> 'Channel':
        channel = Channel()
        channel.type = ChannelType.STARTUP
        return channel