import logging
import schedule
from enum import Enum
from prend.channel import Channel, ChannelType
from prend.rule import Rule
from prend.state import State, StateType


_logger = logging.getLogger(__name__)


class EvalState(Enum):
    GREEN = 0
    ORANGE = 1
    RED = 2  # is also ERROR

    def __str__(self):
        return self.__repr__()

    def __repr__(self) -> str:
        return self.name


class EvalType(Enum):
    # ELEC
    ELEC = 1  # electrical
    OPEN = 2  # opening (door, window)

    def __str__(self):
        return self.__repr__()

    def __repr__(self) -> str:
        return self.name


class EvalItem:
    def __init__(self, eval_type, item_name):
        self.eval_type = eval_type
        self.item_name = item_name

    def __repr__(self) -> str:
        return '{}({},{})'.format(self.__class__.__name__, self.item_name, self.eval_type)


class EvalSet:
    def __init__(self, key, led_item, child_items):
        self.key = key
        self.led_item = led_item
        self.child_items = child_items

    def __repr__(self) -> str:
        return '{}({},{},{})'.format(self.__class__.__name__, self.key, self.led_item, self.child_items)


class LedStatusRule(Rule):

    eval_config = [
        EvalSet('l01', 'valLedHall01', [
            EvalItem(EvalType.OPEN, 'valWinMarc'),
            EvalItem(EvalType.OPEN, 'valWinLara')
        ]),
        EvalSet('r01', 'valLedHall09', [
            EvalItem(EvalType.ELEC, 'valLiMarcCeil'),
            EvalItem(EvalType.ELEC, 'valLiLaraCeil')
        ]),

        EvalSet('l02', 'valLedHall02', [
            EvalItem(EvalType.OPEN, 'valWinGallery'),
            EvalItem(EvalType.OPEN, 'valWinStoreroom')
        ]),
        EvalSet('r02', 'valLedHall10', [EvalItem(EvalType.ELEC, 'valLiStoreroom')]),

        EvalSet('l03', 'valLedHall03', [
            EvalItem(EvalType.OPEN, 'valWinBathUp'),
            EvalItem(EvalType.OPEN, 'valWinSleeping')
        ]),
        EvalSet('r03', 'valLedHall11', [
            EvalItem(EvalType.ELEC, 'valLiBathUpCeil'),
            EvalItem(EvalType.ELEC, 'valLiBathUpMirror'),
            EvalItem(EvalType.ELEC, 'valLiSleeping')
        ]),

        EvalSet('l04', 'valLedHall04', [
            EvalItem(EvalType.OPEN, 'valWinOfficeNorth'),
            EvalItem(EvalType.OPEN, 'valWinOfficeEast')
        ]),
        EvalSet('r04', 'valLedHall12', [
            EvalItem(EvalType.ELEC, 'valLiOfficeIris'),
            EvalItem(EvalType.ELEC, 'valLiOfficeStripeLower'),
            EvalItem(EvalType.ELEC, 'valLiOfficeStripeUpper'),
            EvalItem(EvalType.ELEC, 'valLiOfficeCeil')
        ]),

        EvalSet('l05', 'valLedHall05', [
            EvalItem(EvalType.OPEN, 'valDoorTerrace'),
            EvalItem(EvalType.OPEN, 'valWinLiving'),
            EvalItem(EvalType.OPEN, 'valWinKitchen')
        ]),
        EvalSet('r05', 'valLedHall13', [
            EvalItem(EvalType.ELEC, 'valLiLivingIris'),
            EvalItem(EvalType.ELEC, 'valLiLivingStripe'),
            EvalItem(EvalType.ELEC, 'valLiLivingCorner'),
            EvalItem(EvalType.ELEC, 'valLiLivingCeil'),
            EvalItem(EvalType.ELEC, 'valLiLivingCupboard'),
            EvalItem(EvalType.ELEC, 'valLiKitchen')
        ]),

        EvalSet('l06', 'valLedHall06', [
            EvalItem(EvalType.OPEN, 'valWinBathDown'),
            EvalItem(EvalType.OPEN, 'valWinUtilityRoom')
        ]),
        EvalSet('r06', 'valLedHall14', [
            EvalItem(EvalType.ELEC, 'valLiBathDownCeil'),
            EvalItem(EvalType.ELEC, 'valLiBathDownMirror'),
            EvalItem(EvalType.ELEC, 'valLiUtilityroom')
        ]),

        EvalSet('l07', 'valLedHall07', [EvalItem(EvalType.ELEC, 'valSocketTerrace')]),
        EvalSet('r07', 'valLedHall15', [EvalItem(EvalType.ELEC, 'valLiTerrace')])
    ]

    def __init__(self):
        super().__init__()

        self._child_to_eval = {}
        for eval_set in self.eval_config:
            for eval_item in eval_set.child_items:
                self._child_to_eval[eval_item.item_name] = eval_set

    def register_actions(self) -> None:
        cron_job = schedule.every(5).minutes
        self.subscribe_cron_actions(self.__class__.__name__, cron_job)

        channel = Channel.create_startup()
        self.subscribe_channel_actions(channel)

        for item_name in self._child_to_eval:
            channel = Channel.create_item(item_name)
            self.subscribe_channel_actions(channel)

    def notify_action(self, action) -> None:
        # check for general connection to openhab
        if not self.is_connected():
            _logger.debug('notify_action - NOT CONNECTED - abort')
            return

        _logger.debug('notify_action - %s', action)

        if ChannelType.ITEM == action.channel.type:
            self._update_action_item(action)
        elif ChannelType.CRON == action.channel.type:
            self._update_diff(False)  # issues with homematic - hm thinks that the led are green, but they are not!
        elif ChannelType.STARTUP == action.channel.type:
            self._update_diff(True)

    def _update_action_item(self, action):
        eval_set = self._child_to_eval.get(action.channel.name)
        if not eval_set:
            _logger.error('no eval-set found (%s)!', action)
            return
        self._handle_eval_set(eval_set)

    def _update_diff(self, check_diff_and_update) -> None:
        for eval_set in self.eval_config:
            self._handle_eval_set(eval_set, check_diff_and_update)

    def _handle_eval_set(self, eval_set, check_diff_and_update=False) -> None:
        eval_state = self._check_eval_set(eval_set)

        state_value = self.get_item_state_value(eval_set.led_item)
        if state_value != eval_state.name or not check_diff_and_update:
            self._send_eval_state(eval_set.led_item, eval_state, check_diff_and_update)

    def _send_eval_state(self, led_item, eval_set, check_diff_and_update=False):
        send_command = (not check_diff_and_update)
        channel = Channel.create_item(led_item)
        state = State.create(StateType.STRING, eval_set.name)
        self.send(send_command, channel, state)

    def _check_eval_set(self, eval_set) -> EvalState:
        eval_state = EvalState.GREEN
        for eval_item in eval_set.child_items:
            eval_state = self._check_eval_item(eval_item, eval_state)
        return eval_state

    def _check_eval_item(self, eval_item, eval_state_in) -> EvalState:
        if eval_state_in not in [EvalState.GREEN, EvalState.ORANGE]:
            return eval_state_in

        state = self.get_item_state(eval_item.item_name)
        if state is None:
            _logger.warning('_check_eval_item - item (%s) does not exists!', eval_item.item_name)
            return EvalState.RED

        eval_state_out = None
        try:
            if eval_item.eval_type == EvalType.ELEC:
                if state.is_switched_on():
                    eval_state_out = EvalState.RED
                else:
                    eval_state_out = EvalState.GREEN
            elif eval_item.eval_type == EvalType.OPEN:
                if state.is_tilted():
                    eval_state_out = EvalState.ORANGE
                elif state.is_open():
                    eval_state_out = EvalState.RED
                else:
                    eval_state_out = EvalState.GREEN
        except (TypeError, ValueError):
            eval_state_out = None
            _logger.warning('_check_eval_item failed - cannot evaluate %s for %s', state, eval_item)

        if eval_state_out is None:
            eval_state_out = EvalState.RED
        if eval_state_out.value < eval_state_in.value:
            eval_state_out = eval_state_in

        _logger.debug('_check_eval_item: %s = %s => %s', eval_item, state, eval_state_out)

        return eval_state_out

