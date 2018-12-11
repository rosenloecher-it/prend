from enum import Enum
from prend.channel import Channel, ChannelType
from prend.oh.oh_event import OhEvent, OhNotificationType


class ActionException(Exception):
    pass


class OhIllegalActionException(ActionException):
    def __init__(self, event):
        super().__init__('invalid action ({})!'.format(str(event) if event else 'None'))


class ActionType(Enum):
    CRON = 1
    ITEM = 2
    GROUP = 3
    THING = 4


class Action:

    def __init__(self):
        self.channel = None
        self.listener = None
        self.state_old = None    # type OhValue
        self.state_new = None    # type OhValue
        self.notification_type = None

    def __eq__(self, other) -> bool:
        if not other:
            return False
        if type(self) != type(other):
            return False
        if self.channel != other.channel:
            return False
        if self.listener != other.listener:
            return False
        if self.state_old != other.state_old:
            return False
        if self.state_new != other.state_new:
            return False
        if self.notification_type != other.notification_type:
            return False
        return True

    def __repr__(self) -> str:
        if self.channel and self.channel.type == ChannelType.CRON:
            return '{}({})'.format(self.__class__.__name__, self.channel)
        else:
            return '{}({} | {} => {}; | {} (old: {}))'\
                .format(self.__class__.__name__, self.notification_type, self.channel
                        , self.listener, self.state_new, self.state_old)

    def is_valid(self) -> bool:
        if not self.channel:
            return False
        if not self.channel.is_valid():
            return False
        if self.channel.type != ChannelType.CRON:
            if not self.notification_type:
                return False
            if not self.state_new or not self.state_new.is_valid():
                return False
        return True

    def should_be_published(self) -> bool:
        if self.notification_type == OhNotificationType.ITEM_COMMAND:
            return True
        if self.channel and self.channel.type == ChannelType.CRON:
            return True
        if self.state_old != self.state_new:
            return True
        return False

    @staticmethod
    def create_cron_action(channel_name: str) -> 'Action':
        action = Action()
        action.channel = Channel.create(ChannelType.CRON, channel_name)
        return action

    @staticmethod
    def create_from_event(event: OhEvent)-> 'Action':
        if not event or not event.is_valid():
            raise ActionException('invalid action ({})'.format(str(event) if event else 'None'))

        action = Action()
        action.channel = event.channel
        action.state_new = event.state
        action.notification_type = event.notification_type

        return action


