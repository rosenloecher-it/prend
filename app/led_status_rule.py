import logging
import schedule
from enum import Enum
from prend.channel import Channel, ChannelType
from prend.rule import Rule


_logger = logging.getLogger(__name__)


class EvalState(Enum):
    ERROR = 0  # shown as RED
    GREEN = 1
    ORANGE = 2
    RED = 3

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
            EvalItem(EvalType.ELEC, 'valLiOfficeStripeLower'),
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
        EvalSet('r06', 'valLedHall07', [
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

        if action.channel.type == ChannelType.ITEM:
            self._update_action_item(action)
        elif action.channel.type in [ChannelType.CRON, ChannelType.STARTUP]:
            self._update_diff()

    def _update_action_item(self, action):
        eval_set = self._child_to_eval(action.channel.name)
        if not eval_set:
            _logger.error('no eval-set found (%s)!', action)
            return
        self._handle_eval_set(eval_set)

    def _update_diff(self) -> None:
        for eval_set in self.eval_config:
            self._handle_eval_set(eval_set, True)

    def _handle_eval_set(self, eval_set, check_diff_and_update = False) -> None:
        eval_state = self._check_eval_set(eval_set)
        self._send_eval_state(eval_state, check_diff_and_update)

    def _send_eval_state(self, eval_set, check_diff_and_update = False):
        pass

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
            return EvalState.ERROR

        eval_state_out = None
        try:
            if eval_item.eval_type == EvalType.ELEC:
                if state.is_switched_on():
                    eval_state_out = EvalState.RED
            elif eval_item.eval_type == EvalType.OPEN:
                if state.is_tilted():
                    eval_state_out = EvalState.ORANGE
                elif state.is_open():
                    eval_state_out = EvalState.RED
            elif eval_item.eval_type == EvalType.DOOR:
                if state.is_open():
                    eval_state_out = EvalState.RED
        except ValueError:
            eval_state_out = None
            _logger.warning('_check_eval_item failed - cannot evaluate %s for %s', state, eval_item)

        if eval_state_out is None:
            eval_state_out = EvalState.ERROR
        if eval_state_out < eval_state_in:
            eval_state_out = eval_state_in

        _logger.debug('_check_eval_item: %s = %s => %s', eval_item, state, eval_state_out)

        return eval_state_out



#
# // 0 == zu; 1 = offen
# val Functions$Function3<String, GenericItem, Number, Number> determineStatusWindow01 =
#     [ logClass, itemWindows01, stateWindowsIn |
#             val String logKey = "determineStatusWindow01(" + itemWindows01.name + ") - "
#             var Number stateWindows = stateWindowsIn
#
# 			if (itemWindows01 !== null) {
# 			// TODO change
#             //if (itemWindows01 !== null && itemWindows01 !== NULL) {
#                 //logKey = logKey + itemWindows01.name
#
#                 var Number stateWindow = 2
#
#                 if (itemWindows01.state !== NULL) {
#                 	var Number value = (itemWindows01.state as Number).intValue()
#                 	if (value == 0) stateWindow = 0
#                 }
#
#                 if (stateWindows < stateWindow ) { stateWindows = stateWindow; }
#
#                 //logDebug(logClass, logKey + " - out: " + String::format("%s == %d => stateWindows = %d", value, stateWindow, stateWindows))
#             }
#             else {
#                 logError(logClass, logKey + " itemWindows01 is NULL!")
#                 stateWindows = 2
#             }
#
#             return stateWindows
#     ]
#
#
# // Number stateWindows; 0 = CLOSED (Standard); 1 = TILTED; 2 = OPEN
# val Functions.Function3<String, StringItem, Number, Number> determineStatusWindowsHandle =
#     [ logClass, itemWindowsHandle, stateWindowsIn |
#             val String logKey = "determineStatusWindowsHandle(" + itemWindowsHandle.name + ") - "
#             var Number stateWindows = stateWindowsIn
#
#             var Number stateWindow = 2
#             val String value = itemWindowsHandle.state.toString
#
#             if (value == "CLOSED")
#                 stateWindow = 0
#             else if (value == "TILTED")
#                 stateWindow = 1
#             else if (value != "NULL" && value != "OPEN")
#                 logWarn(logClass, logKey + " unknown value: " + String::format("%s == %d => stateWindows = %d", value, stateWindow, stateWindows))
#
#             if (stateWindows < stateWindow)
#                 stateWindows = stateWindow;
#
#             logDebug(logClass, logKey + "out: " + String::format("%s == %d => stateWindows = %d", value, stateWindow, stateWindows))
#
#             return stateWindows
#     ]
#
#
# // Number stateWindows; 0 = OFF; 2 = ON
# val Functions$Function3<String, GenericItem, Number, Number> determineStatusOnOff =
#     [ logClass, itemOnOff, stateWindowsIn |
#             val String logKey = "determineStatusOnOff(" + itemOnOff.name + ") - "
#             var Number stateWindows = stateWindowsIn
#
#             if (itemOnOff !== null && itemOnOff.state !== NULL) {
#                 //logKey = logKey + itemOnOff.name
#
#                 var Number stateWindow = 2
#                 var String value = itemOnOff.state.toString
#                 //logDebug(logClass, logKey + String.format("%s=%s", itemOnOff.name, value))
#
#                 if (value == "OFF") { stateWindow = 0 }
#
#                 if (stateWindows < stateWindow ) { stateWindows = stateWindow; }
#
#                 logDebug(logClass, String::format("%s%s == %d => stateWindows = %d", logKey, value, stateWindow, stateWindows))
#             }
#             else {
#                 logWarn(logClass, String.format("%s itemOnOff.state is %s!", logKey, itemOnOff.state.toString))
#                 stateWindows = 2
#             }
#
#             return stateWindows
#     ]
#
# // Number stateWindows; value==0 => OFF; >0 => ON
# val Functions$Function3<String, GenericItem, Number, Number> determineStatusNumber =
#     [ logClass, itemOnOff, stateWindowsIn |
#             val String logKey = "determineStatusNumber(" + itemOnOff.name + ") - "
#             var Number stateWindows = stateWindowsIn
#
#             logDebug(logClass, String::format("%s ", logKey))
#
#             if (itemOnOff !== null && itemOnOff.state !== NULL) {
#
#                 logDebug(logClass, String::format("%s %s => stateWindows = ", logKey, itemOnOff.state.toString))
#
#                 if (itemOnOff.state instanceof Number) {
#                     val value = itemOnOff.state as Number
#                     var Number stateWindow = 2
#                     if (value < 0.001 && value > -0.001)
#                         stateWindow = 0
#
#                     if (stateWindows < stateWindow )
#                         stateWindows = stateWindow;
#                 } else {
#                     stateWindows = 2
#                     logError(logClass, logKey + "itemOnOff.state is NO Number valid!")
#                 }
#
#                 logDebug(logClass, String::format("%s %s => stateWindows = ", logKey, itemOnOff.state.toString))
#
#                 logDebug(logClass, String::format("%s %s => stateWindows = %d", logKey, itemOnOff.state.toString, stateWindows))
#             }
#             else {
#                 logError(logClass, logKey + "itemOnOff.state is NOT valid!")
#                 stateWindows = 2
#             }
#
#             return stateWindows
#     ]
#
# // 0 GREEN; 1 ORANGE; 2 nzw. sonst RED
# val Functions$Function3<String, StringItem, Number, String> setLedStatus =
#     [ logClass, itemLed, stateWindows |
#             val String logKey = "setLedStatus - "
#             if (itemLed !== null && itemLed != NULL) {
#                 //logKey = logKey + itemLed.name
#
#                 //! LED-Statusanzeige (16-fach): HM-OU-LED16: 0 aus; 1 rot; 2 grün; 3 orange
#                 var String stateOut = "RED";
#                 if ( stateWindows == 0) {
#                     stateOut = "GREEN";
#                 } else if ( stateWindows == 1) {
#                     stateOut = "ORANGE";
#                 }
#
#                 itemLed.sendCommand(stateOut)
#
#                 return stateOut
#             }
#             else {
#                 logDebug(logClass, logKey + " itemLed is NULL!")
#
#                 return "ERROR"
#             }
#     ]

