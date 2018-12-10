from enum import Enum
import datetime
import dateutil.parser
import typing
from prend.values import OnOffValue, OnlineOfflineValue


class StateType(Enum):
    UNDEF = 1  # NOT undefined AND NOT None - will be delivered by openhab!
    DECIMAL = 2  # could be switched to DIMMER or ROLLERSHUTTER
    DIMMER = 3
    STRING = 4
    ONOFF = 5  # can be SWITCH or CONTACT
    SWITCH = 6
    CONTACT = 7
    DATETIME = 8
    COLOR = 9
    ROLLERSHUTTER = 10
    GROUP = 11  # value type undefined => string
    THING = 12

    def __str__(self):
        return self.__repr__()

    def __repr__(self) -> str:
        return self.name

    @staticmethod
    def parse(text) -> typing.Optional['StateType']:
        result = None

        if text:
            text = text.strip().upper()
            for en in StateType:
                if en.name == text:
                    result = en
                    break
            if not result and text == 'NUMBER':
                result = StateType.DECIMAL

        return result


class State:

    def __init__(self) -> None:
        self.type = None
        self.value = None
        self.last_change = None

        self.update_last_change()

    def __repr__(self) -> str:
        return '{}({},{})'.format(self.__class__.__name__, self.type, self.value)

    def __eq__(self, other) -> bool:
        if not other:
            return False
        if type(self) != type(other):
            return False
        if self.type != other.type:
            return False
        if self.value != other.value:
            return False
        return True

    def is_valid(self) -> bool:
        if not self.type:
            return False
        return True

    def update_last_change(self) -> None:
        self.last_change = datetime.datetime.now()

    def import_state(self, other) -> None:
        if self.type != StateType.UNDEF and other.type == StateType.UNDEF:
            self.value = None
        if self.type in [StateType.CONTACT, StateType.SWITCH] and other.type == StateType.ONOFF:
            # don't overwrite type
            self.value = other.value
        if self.type in [StateType.DIMMER, StateType.ROLLERSHUTTER] and other.type == StateType.DECIMAL:
            # don't overwrite type
            self.value = other.value
        else:
            self.type = other.type
            self.value = other.value
        self.last_change = other.last_change or datetime.datetime.now()

    def import_newer_state(self, other) -> None:
        if not other:
            return
        if self.last_change and not other.last_change:
            return
        if self.last_change > other.last_change:
            return
        self.import_state(other)

    # noinspection PyShadowingBuiltins
    @staticmethod
    def create(state_type, value, last_change=None) -> 'State':
        state = State()
        state.type = state_type
        state.value = value
        state.last_change = last_change or datetime.datetime.now()
        return state

    @staticmethod
    def convert_to_value(state_type, value_in):
        value_out = value_in

        if value_in:
            if value_in in ['NULL', 'UNDEF']:
                value_out = None
            elif state_type in [StateType.STRING, StateType.GROUP, StateType.COLOR]:
                value_out = str(value_in)
            elif state_type in [StateType.DECIMAL, StateType.DIMMER, StateType.ROLLERSHUTTER]:
                value_out = float(value_in)
            elif state_type in [StateType.CONTACT, StateType.ONOFF, StateType.SWITCH]:
                value_out = OnOffValue.parse(value_in)
            elif state_type == StateType.THING:
                value_out = OnlineOfflineValue.parse(value_in)
            elif state_type == StateType.DATETIME:
                value_out = dateutil.parser.parse(value_in)
            elif state_type == StateType.UNDEF:
                value_out = None

        return value_out

    # noinspection PyUnusedLocal
    @staticmethod
    def convert_to_json(value_in):
        value_out = value_in

        if value_in is None:
            value_out = 'UNDEF'
        elif type(value_in) == datetime.datetime:
            value_out = value_in.isoformat()
        elif type(value_in) is OnOffValue:
            value_out = value_in.name
        elif type(value_in) is OnlineOfflineValue:
            value_out = value_in.name

        else:
            value_out = str(value_in)

        return value_out
