import datetime
import logging
import schedule
from prend.channel import Channel, ChannelType
from prend.rule import Rule
from .fronstor_requester import FronstorRequester
from app.fronstor.fronstor_extracter import FronstorExtracter, FronstorStatus
from .fronstor_constants import FronstorConstants


_logger = logging.getLogger(__name__)


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



    # (overwriten) register your notifications and do some initialisation
    def register_actions(self) -> None:
        _logger.info('register_actions')

        # # _logger.info('show config: {}'.format(self._config))
        # # better access config via self.get_config*
        #
        # # create cron job - syntax see https://github.com/dbader/schedule
        # cron_job = schedule.every().minute
        # # choose a cron name to recognize several cron jobs
        # self.subscribe_cron_actions('cron_name_1', cron_job)
        #
        # # create channel object and subscribe for changes
        # channel = Channel.create(ChannelType.ITEM, 'dummy_number')
        # self.subscribe_openhab_actions(channel)
        #
        # # create channel obect and subscribe for changes
        # channel = Channel.create(ChannelType.ITEM, 'dummy_switch')
        # self.subscribe_openhab_actions(channel)


    # all notification will be sent here
    def notify_action(self, action) -> None:

        # check for general connection to openhab
        if not self.is_connected():
            _logger.debug('notify_action - NOT CONNECTED - %s', action)
            return

        if not self._is_battery_active():
            _logger.debug('notify_action - battery not active - %s', action)
            return

        _logger.debug('notify_action - %s', action)

        json = self._requester.request()
        self.last_extract = self._extracter.extract(json)
        if self.last_extract.status == FronstorStatus.SUCCESS:
            self.send_values(self.last_extract.values)



            # # get item state
            # dummy_number = self.get_item_state_value('dummy_number')
            #
            # if dummy_number is None:
            #     dummy_number = 1
            #     self.send_item_command('dummy_number', dummy_number)
            #
            # # send command to another item (there is also a "send_item_update")
            # self.send_item_command('dummy_number_2', dummy_number)
            #
            # # send another command
            # text = '{} ({})'.format(dummy_number, datetime.datetime.now().isoformat())
            # self.send_item_command('dummy_string', text)



    def _is_battery_active(self):
        battery_state = self.get_value(FronstorConstants.ITEM_BAT_STATE)
        battery_active = False

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
        for key, newValue in values.items():
            currItem = self.values.get(key)

            self.get_item_state_value('dummy_number')


            if currItem == None:
                print('error: openhab item ({}) not found!'.format(key))
            else:
                currValue = currItem.state
                if currValue != newValue:
                    print('openhab item ({}) found (current={} != new={})'.format(key, currValue, newValue))
                    self.send_item_command(key, newValue)
                else:
                    print('openhab item ({}) found (current={} != new={}) => no change'.format(key, currValue, newValue))


# class FroniusStorageRule(Rule):
#
#
#     def process(self):
#         try:
#
#             print('load openhab values')
#             self.openhab.load_values()
#             print('request service')
#             json = self.requester.request()
#             print('extract json')
#             self.last_extract = self.extracter.extract(json)
#             if self.last_extract.status == Status.SUCCESS:
#                 print('values extracted => send values')
#                 self.openhab.send_values(self.last_extract.values)
#         finally:
#             self.openhab.close()
#
#     def get_last_extract(self):
#         return self.last_extract

