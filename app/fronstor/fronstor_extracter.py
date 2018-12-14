import logging
import traceback
from enum import Enum
from collections import namedtuple
from .fronstor_constants import FronstorConstants


_logger = logging.getLogger(__name__)


class FronstorStatus(Enum):
    ERROR = 1
    OFF = 2
    SUCCESS = 3


class FronstorExtracter:

    def get_deep_attribute(self, json_data, keys):
        len_attributes = len(keys)
        if len_attributes < 1:
            return None

        key = keys[0]

        if isinstance(key, int):
            attribute = json_data[key]
        else:
            attribute = json_data.get(keys[0])

        if len_attributes == 1 or attribute is None:
            return attribute
        else:
            sub_keys = keys[1:]
            return self.get_deep_attribute(attribute, sub_keys)

    @staticmethod
    def _store_value(datadict, channel, value):
        datadict[channel] = value
        # _logger.debug("store json value: %s = %s", channel, value)

    def _find_temp_and_cycle(self, json_data):
        result = {}
        temp_inv = self.get_deep_attribute(json_data, ['Body', 'Data', '0', 'Controller', 'Temperature_Cell'])
        self._store_value(result, FronstorConstants.ITEM_INV_TEMP, temp_inv)

        json_mods = self.get_deep_attribute(json_data, ['Body', 'Data', '0', 'Modules'])

        if isinstance(json_mods, list):
            len_json_mods = len(json_mods)
            if len_json_mods != FronstorConstants.ITEM_BAT_COUNT:
                _logger.warning('warning: count batteries (%d) does not match configured count  (%d)!'
                                , len_json_mods, FronstorConstants.ITEM_BAT_COUNT)

        temp_max = None
        cycle_min = None
        cycle_max = None

        for i in range(0, FronstorConstants.ITEM_BAT_COUNT):
            item_temp = FronstorConstants.ITEM_BAT_TEMP_FORMAT.format(i + 1)
            item_cycle = FronstorConstants.ITEM_BAT_CYCLE_FORMAT.format(i + 1)

            temp_mod = self.get_deep_attribute(json_data
                                               , ['Body', 'Data', '0', 'Modules', i, 'Temperature_Cell_Maximum'])
            self._store_value(result, item_temp, temp_mod)
            if temp_mod is not None:
                if temp_max is None or temp_mod > temp_max:
                    temp_max = temp_mod

            cycle_mod = self.get_deep_attribute(json_data
                                                , ['Body', 'Data', '0', 'Modules', i, 'CycleCount_BatteryCell'])
            if cycle_mod is not None:
                # don't overwrite real cycle values with None
                self._store_value(result, item_cycle, cycle_mod)
                if cycle_max is None or cycle_mod > cycle_max:
                    cycle_max = cycle_mod
                if cycle_min is None or cycle_mod < cycle_min:
                    cycle_min = cycle_mod

        self._store_value(result, FronstorConstants.ITEM_BAT_TEMP_MAX, temp_max)

        if cycle_min is not None or cycle_max is not None:
            if cycle_min is None:
                cycle_min = '?'
            if cycle_max is None:
                cycle_max = '?'
            self._store_value(result, FronstorConstants.ITEM_BAT_CYCLE_SPAN, '{}-{}'.format(cycle_min, cycle_max))

        return result

    def extract(self, json_data):

        message = None
        values = None

        status_code = self.get_deep_attribute(json_data, ['Head', 'Status', 'Code'])
        if status_code != 0:
            status = FronstorStatus.ERROR
            message = self.get_deep_attribute(json_data, ['Head', 'Status', 'Reason'])
            message2 = self.get_deep_attribute(json_data, ['Head', 'Status', 'UserMessage'])
            _logger.error("extract failure - status: %s | message: %s ({})", status, message, message2)

        else:
            try:
                values = self._find_temp_and_cycle(json_data)
                status = FronstorStatus.SUCCESS

            except AttributeError as ex:
                status = FronstorStatus.ERROR
                _logger.error('extract failed (%s)', ex)

        Result = namedtuple('Result', ['status', 'message', 'values'])
        result = Result(status, message, values)
        return result

