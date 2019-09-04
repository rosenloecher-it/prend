import copy
from enum import IntFlag
from prend.channel import Channel, ChannelType
from prend.state import State


class OhSendFlags(IntFlag):
    NONE = 0
    COMMAND = 0x01
    UPDATE = 0x02
    SEND_ONLY_IF_DIFFER = 0x04
    CHANNEL_AS_ITEM = 0x08
    SKIP_CHANNEL_CHECK = 0x10


class OhSendData:
    def __init__(self, flags: OhSendFlags, channel, state):
        self.flags = flags

        if channel is None:
            self.channel = None
        else:
            self.channel = copy.deepcopy(channel)

        if state is None:
            self.state = None
        else:
            self.state = copy.deepcopy(state)

    def __repr__(self) -> str:
        return '{}({},{},{})'.format(self.__class__.__name__, hex(self.flags) if self.flags is not None else 'None'
                                     , self.channel, self.state)

    def check(self):
        channel = self.get_channel()
        if not channel:
            raise ValueError('channel is None')
        if not channel.is_valid():
            raise ValueError('invalid channel')
        if channel.type not in [ChannelType.ITEM, ChannelType.GROUP]:
            raise ValueError()

        count = 0
        if self.flags & OhSendFlags.COMMAND:
            count += 1
        if self.flags & OhSendFlags.UPDATE:
            count += 1
        if count != 1:
            raise ValueError('use one of COMMAND or UPDATED!')

    def is_flag(self, flag: OhSendFlags):
        return self.flags & flag

    def is_send(self):
        return self.flags & OhSendFlags.COMMAND

    def is_update(self):
        return self.flags & OhSendFlags.UPDATE

    def get_channel(self):
        if self.channel is None:
            raise ValueError('no channel')
        if self.flags & OhSendFlags.CHANNEL_AS_ITEM:
            if isinstance(self.channel, str):
                channel = Channel.create_item(self.channel)
                return channel
            raise ValueError()

        if isinstance(self.channel, Channel):
            return self.channel

        raise ValueError()

    def get_state_value(self):
        if type(self.state) is State:
            return self.state.value
        else:
            return self.state

    def does_state_value_differ(self, comp):
        if type(self.state) is State:
            value_self = self.state.value
        else:
            value_self = self.state

        if type(comp) is State:
            value_comp = comp.value
        else:
            value_comp = comp

        return value_self != value_comp
