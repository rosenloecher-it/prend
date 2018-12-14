import datetime
import logging
import schedule
from prend.channel import Channel, ChannelType
from prend.rule import Rule
from .fronstor_requester import FronstorRequester
from app.fronstor.fronstor_extracter import FronstorExtracter, FronstorStatus
from .fronstor_constants import FronstorConstants


_logger = logging.getLogger(__name__)


class FronstorException(Exception):
    pass


class FronstorRule(Rule):

    def __init__(self):
        self._requester = None
        self._extracter = None
        pass

    def set_requester(self, requester):
        self._requester = requester

    def set_extracter(self, extracter):
        self._extracter = extracter

    def open(self):

        if not self._requester:
            self._requester = FronstorRequester()
        if not self._extracter:
            self._extracter = FronstorExtracter()

    def register_actions(self) -> None:
        cron_job = schedule.every().minute
        self.subscribe_cron_actions(self.__class__.__name__, cron_job)

        self.subscribe_openhab_actions(Channel.create_startup())

    def notify_action(self, action) -> None:
        try:
            # check for general connection to openhab
            if not self.is_connected():
                _logger.debug('notify_action - NOT CONNECTED - abort')
                return

            if not self._is_battery_active():
                _logger.debug('notify_action - battery not active - abort')
                return

            _logger.debug('notify_action - %s', action)

            json = self._requester.request()
            self.last_extract = self._extracter.extract(json)
            if self.last_extract.status == FronstorStatus.SUCCESS:
                self.send_values(self.last_extract.values)

        except FronstorException as ex:
            _logger.error('notify_action failed - %s', ex)

    def _is_battery_active(self):
        channel = Channel.create_item(FronstorConstants.ITEM_BAT_STATE)
        battery_state = self.get_state(channel)
        battery_state_value = battery_state.ensure_value_int()
        if battery_state_value is None:
            raise FronstorException('no battery state ({}; {}) available!'.format(channel, battery_state))

        try:
            # valid
            # 3=(3) DISCHARGE
            # 4=(4) CHARGING
            # 5=(5) FULL
            # 6=(6) HOLDING
            # 7=(7) TESTING
            num_state = float(battery_state)
            if num_state >= 3 and num_state <= 7:
                battery_active = True
        except ValueError as e:
            _logger.error('is_battery_active: cannot convert battery (%s) state to float! => no active', battery_state)
            battery_active = False

        return battery_active

    def send_values(self, values):

        class ItemData:
            def __init__(self):
                self.channel = None
                self.state = None
                pass
        items = []

        for key, new_value in values.items():
            item = ItemData()
            item.channel = Channel.create_item(key)
            item.state = self.get_item_state(item.channel)
            if not item.state:
                raise FronstorException('openhab state ({}) not found!'.format(item.channel))
            if item.state.value == new_value:
                _logger.debug('found equal values: item ({}) - current={} == new={} => skip'.format(key, item.state.value, new_value))
                continue
            if not item.state.set_value_check_type(new_value):
                raise FronstorException('cannot set state ({}) not found!'.format(item.channel))
            items.append(item)

        for item in items:
            # logging is done in OhRest
            self.send_item_command(item.channel, item.state)


