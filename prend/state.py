import datetime
import dateutil.parser
import logging
from enum import Enum
from prend.values import FormatToJson, OnOffValue, ThingStatusValue, UpDownValue, HsbValue, OpeningValue
from typing import Optional


_logger = logging.getLogger(__name__)


class StateType(Enum):
    UNDEF = 1  # NOT undefined AND NOT None - will be delivered by openhab!
    UNKNOWN = 2  # types not listed here, will be collected as unknown
    CONTACT = 4
    DATETIME = 5
    DECIMAL = 6  # could be switched to DIMMER or ROLLERSHUTTER
    DIMMER = 7
    GROUP = 8  # value type undefined => string
    HSB = 9  # color
    ONOFF = 10  # can be SWITCH or CONTACT
    PERCENT = 11
    ROLLERSHUTTER = 12
    STRING = 13
    SWITCH = 14
    THING_STATUS = 15
    UPDOWN = 16

    def __str__(self):
        return self.__repr__()

    def __repr__(self) -> str:
        return self.name

    def is_number_type(self):
        if self in [StateType.DECIMAL, StateType.DIMMER, StateType.ROLLERSHUTTER, StateType.PERCENT]:
            return True
        return False

    @staticmethod
    def parse(text) -> Optional['StateType']:
        result = None

        if text:
            text = text.strip().upper()
            for en in StateType:
                if en.name == text:
                    result = en
                    break
            if not result and text == 'NUMBER':
                result = StateType.DECIMAL
            elif not result and text == 'COLOR':
                result = StateType.HSB
            elif not result and text == 'THING':
                result = StateType.THING_STATUS

        if not result:
            result = StateType.UNKNOWN

        return result


class State:

    def __init__(self) -> None:
        self.type = None  # type: StateType
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

    def ensure_value_int(self) -> int:
        value_int = None
        if self.value:
            if isinstance(self.value, int):
                value_int = self.value
            # convert from float
            elif self.type.is_number_type():
                try:
                    value_int = int(self.value)
                except ValueError:
                    value_int = None
        return value_int

    def ensure_value_float(self) -> float:
        value_float = None
        if self.value:
            if isinstance(self.value, float):
                value_float = self.value
            elif self.type.is_number_type():
                try:
                    value_float = float(self.value)
                except ValueError:
                    value_float = None
        return value_float

    def update_last_change(self) -> None:
        self.last_change = datetime.datetime.now()

    def set_value(self, value) -> None:
        self.value = value
        self.update_last_change()

    def set_value_check_type(self, value) -> bool:
        type_matches = False
        if isinstance(self.value, int):
            if self.type.is_number_type():
                type_matches = True
        elif isinstance(self.value, float):
            if self.type.is_number_type():
                type_matches = True
        else:
            type_matches = True

        if type_matches:
            self.set_value(value)
        return type_matches

    def import_state(self, other) -> None:
        if self.type != StateType.UNDEF and other.type == StateType.UNDEF:
            self.value = None
        elif self.type in [StateType.CONTACT, StateType.SWITCH] and other.type == StateType.ONOFF:
            # don't overwrite type
            self.value = other.value
        elif self.type in [StateType.DIMMER, StateType.ROLLERSHUTTER] and other.type == StateType.DECIMAL:
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
    def convert(state_type: Optional[str], state_text: Optional[str]) -> 'State':

        state = State()

        try:
            state.type = StateType.parse(state_type)

            if state_text:
                if state_text in ['NULL', 'UNDEF']:
                    state.value = None
                elif state.type in [StateType.STRING, StateType.GROUP, StateType.UNKNOWN]:
                    state.value = str(state_text)
                elif state.type in [StateType.DECIMAL, StateType.DIMMER, StateType.ROLLERSHUTTER]:
                    state.value = float(state_text)
                elif state.type in [StateType.CONTACT, StateType.ONOFF, StateType.SWITCH]:
                    state.value = OnOffValue.parse(state_text)
                elif state.type == StateType.HSB:
                    state.value = HsbValue.parse(state_text)
                elif state.type == StateType.PERCENT:
                    state.value = int(state_text)
                elif state.type == StateType.UPDOWN:
                    state.value = UpDownValue.parse(state_text)
                elif state.type == StateType.THING_STATUS:
                    state.value = ThingStatusValue.parse(state_text)
                elif state.type == StateType.DATETIME:
                    state.value = dateutil.parser.parse(state_text)
                elif state.type == StateType.UNDEF:
                    state.value = None
                else:
                    _logger.error('cannot convert - unknown state type: ', state_type)
                    raise ValueError()

        except ValueError:
            state.type = StateType.UNKNOWN
            state.value = str(state_text)

        state.update_last_change()

        return state

    # noinspection PyUnusedLocal
    @staticmethod
    def convert_to_json(value_in):
        value_out = value_in

        if value_in is None:
            value_out = 'UNDEF'

        elif isinstance(value_in, FormatToJson):
            value_out = value_in.format_to_json()
        elif isinstance(value_in, datetime.datetime):
            t1 = value_in.strftime("%Y-%m-%dT%H:%M:")
            t2 = "{:06.3f}".format(value_in.second + value_in.microsecond / 1e6)
            t3 = value_in.strftime("%z")
            value_out = "{}{}{}".format(t1, t2, t3)
        elif isinstance(value_in, Enum):
            value_out = value_in.name
        else:
            value_out = str(value_in)

        return value_out

    def is_switched_off(self) -> bool:
        return not self.is_switched_on()

    def is_switched_on(self) -> bool:
        if self.value is None:
            raise ValueError()
        if isinstance(self.value, OnOffValue):
            if OnOffValue.OFF == self.value:
                return False
            elif OnOffValue.ON == self.value:
                return True
            raise ValueError()
        elif self.type in [StateType.DIMMER, StateType.DECIMAL, StateType.PERCENT]:
            conv = int(self.value)
            if conv == 0:
                return False
            elif conv > 0:
                return True
            raise ValueError()
        elif StateType.HSB == self.type:
            return self.value.is_on()
        # you should NOT come here, some cases are missing
        raise ValueError()

    # window, door
    def is_closed(self) -> bool:
        if self.value is None:
            raise ValueError()
        if StateType.STRING == self.type:
            typed_value = OpeningValue.parse(self.value)
            return typed_value == OpeningValue.CLOSED
        elif StateType.DECIMAL == self.type:
            conv = int(self.value)
            if conv == 0:
                return True
            elif conv > 0:
                return False
        # you should NOT come here, some cases are missing
        raise ValueError()

    # window, door
    def is_open(self) -> bool:
        if self.value is None:
            raise ValueError()
        if StateType.STRING == self.type:
            typed_value = OpeningValue.parse(self.value)
            return typed_value != OpeningValue.CLOSED
        elif StateType.DECIMAL == self.type:
            conv = int(self.value)
            if conv == 0:
                return False
            elif conv > 0:
                return True
            raise ValueError()
        # you should NOT come here, some cases are missing
        raise ValueError()

    # window, door
    def is_tilted(self) -> bool:
        if self.value is None:
            raise ValueError()
        if StateType.STRING == self.type:
            typed_value = OpeningValue.parse(self.value)
            return typed_value == OpeningValue.TILTED
        elif StateType.DECIMAL == self.type:
            return False  # no items exists!
        # you should NOT come here, some cases are missing
        raise ValueError()
