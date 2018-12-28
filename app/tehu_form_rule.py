import datetime
import locale
import logging
import schedule
from prend.channel import Channel, ChannelType
from prend.rule import Rule
from prend.state import State, StateType


_logger = logging.getLogger(__name__)


class ItemSet:

    def __init__(self, show, temp, humi):
        self.temp = temp
        self.humi = humi
        self.show = show
        self.last_update = None


class TehuFormRule(Rule):

    TIME_SHOW_REFRESH_WARNING_SEC = 1200

    def __init__(self):
        super().__init__()

        self._item_set_list = [
            ItemSet('showTempHumiBathDown', 'valTempBathDown', 'valHumiBathDown'),
            ItemSet('showTempHumiLiving', 'valTempLiving', 'valHumiLiving'),
            ItemSet('showTempHumiMarc', 'valTempMarc', 'valHumiMarc'),
            ItemSet('showTempHumiNorthSide', 'valTempNorthSide', 'valHumiNorthSide'),
            ItemSet('showTempHumiOffice', 'valTempOffice', 'valHumiOffice'),
            ItemSet('showTempHumiRoofStat', 'valTempRoofStat', 'valHumiRoofStat'),
            ItemSet('showTempHumiSleeping', 'valTempSleeping', 'valHumiSleeping')
        ]

    def register_actions(self) -> None:
        _logger.debug('register_actions')

        cron_job = schedule.every(15).minutes
        self.subscribe_cron_actions(self.__class__.__name__, cron_job)

        channel = Channel.create_startup()
        self.subscribe_channel_actions(channel)

        time_startup = datetime.datetime.now()
        for item_set in self._item_set_list:
            channel = Channel.create(ChannelType.ITEM, item_set.temp)
            self.subscribe_channel_actions(channel)

            channel = Channel.create(ChannelType.ITEM, item_set.humi)
            self.subscribe_channel_actions(channel)

            item_set.last_change = time_startup

    def notify_action(self, action) -> None:

        # check for general connection to openhab
        if not self.is_connected():
            _logger.debug('notify_action - NOT CONNECTED - %s', action)
            return

        if action.channel.type == ChannelType.ITEM:
            self._update_action_item(action)
        elif action.channel.type == ChannelType.CRON:
            self._update_not_working()
        elif action.channel.type == ChannelType.STARTUP:
            self._update_all()

    def _get_item_set(self, item_name):
        found = None
        for item_set in self._item_set_list:
            if item_set.temp == item_name or item_set.humi == item_name:
                found = item_set
                break
        return found

    @classmethod
    def _format_number(cls, state, is_humi) -> str:
        text = None
        try:
            if state and state.value is not None:
                diff_seconds = (datetime.datetime.now() - state.last_change).total_seconds()
                if diff_seconds > cls.TIME_SHOW_REFRESH_WARNING_SEC:
                    warn = '!'
                else:
                    warn = ''

                if is_humi:
                    text_number = locale.format("%.0f", state.value)
                    text = '{}{} %'.format(warn, text_number)
                else:
                    text_number = locale.format("%.1f", state.value)
                    text = '{}{} °C'.format(warn, text_number)

        except ValueError:
            text = None
        if text is None:
            text = '-'

        return text

    def _handle_item_set(self, item_set):
        state_temp = self.get_item_state(item_set.temp)
        state_humi = self.get_item_state(item_set.humi)

        text_temp = self._format_number(state_temp, False)
        text_humi = self._format_number(state_humi, True)

        state = State.create(StateType.STRING, None)
        state.value = '{} / {}'.format(text_temp, text_humi)
        self.send_item_command(item_set.show, state)

        item_set.last_update = datetime.datetime.now()

    def _update_action_item(self, action):
        item_set = self._get_item_set(action.channel.name)
        if not item_set:
            _logger.error('no item-set found (%s)!', action)
            return
        self._handle_item_set(item_set)

    def _update_not_working(self):
        for item_set in self._item_set_list:
            diff_seconds = (datetime.datetime.now() - item_set.last_update).total_seconds()
            if diff_seconds > self.TIME_SHOW_REFRESH_WARNING_SEC:
                self._handle_item_set(item_set)

    def _update_all(self):
        for item_set in self._item_set_list:
            self._handle_item_set(item_set)


