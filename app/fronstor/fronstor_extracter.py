import json
import traceback
from enum import Enum
from collections import namedtuple
from .fronstor_constants import FronstorConstants


class FronstorStatus(Enum):
    ERROR = 1
    OFF = 2
    SUCCESS = 3



class FronstorExtracter:

    def get_deep_attribute(self, json, keys):
        lenAttributes = len(keys)
        if lenAttributes < 1:
            return None

        key = keys[0]

        if isinstance(key, int):
            attribute = json[key]
        else:
            attribute = json.get(keys[0])

        if lenAttributes == 1 or attribute == None:
            return attribute
        else:
            subKeys = keys[1:]
            return self.get_deep_attribute(attribute, subKeys)

    def store_value(self, dict, channel, value):
        dict[channel] = value
        print("store json value: {} = {}".format(channel, value))

    def find_temp_and_cycle(self, json):
        result = {}
        tempInv = self.get_deep_attribute(json, ['Body', 'Data', '0', 'Controller', 'Temperature_Cell'])
        self.store_value(result, FronstorConstants.ITEM_INV_TEMP, tempInv)

        jsonMods = self.get_deep_attribute(json, ['Body', 'Data', '0', 'Modules'])

        lenJsonMods = -1
        if isinstance(jsonMods, list):
            lenJsonMods = len(jsonMods)
            if lenJsonMods != FronstorConstants.ITEM_BAT_COUNT:
                print('warning: count batteries ({}) does not match configured count  ({})!'.format(lenJsonMods, Constants.item_bat_count))

        tempMax = -1
        cycleMin = -1
        cycleMax = -1

        for i in range(0, FronstorConstants.ITEM_BAT_COUNT):
            itemTemp = FronstorConstants.ITEM_BAT_TEMP_FORMAT.format(i + 1)
            itemCycle = FronstorConstants.ITEM_BAT_CYCLE_FORMAT.format(i + 1)

            tempMod = None
            cycleMod = None
            if i < lenJsonMods:
                tempMod = self.get_deep_attribute(json, ['Body', 'Data', '0', 'Modules', i, 'Temperature_Cell_Maximum'])
                cycleMod = self.get_deep_attribute(json, ['Body', 'Data', '0', 'Modules', i, 'CycleCount_BatteryCell'])
                if tempMod > tempMax:
                    tempMax = tempMod
                if cycleMod > cycleMax:
                    cycleMax = cycleMod
                if cycleMod < cycleMin or cycleMin < 0 and cycleMod > 0:
                    cycleMin = cycleMod

            self.store_value(result, itemTemp, tempMod)
            self.store_value(result, itemCycle, cycleMod)

        if tempMax > 0:
            self.store_value(result, FronstorConstants.ITEM_BAT_TEMP_MAX, tempMax)
        else:
            self.store_value(result, FronstorConstants.ITEM_BAT_TEMP_MAX, None)

        if cycleMin < 0:
            cycleMin = '?'
        if cycleMax < 0:
            cycleMax = '?'

        self.store_value(result, FronstorConstants.ITEM_BAT_CYCLE_SPAN, "{}-{}".format(cycleMin, cycleMax))

        return result


    def extract(self, json):

        status = FronstorStatus.ERROR
        message = None
        values = None

        statusCode = self.get_deep_attribute(json, ['Head', 'Status', 'Code'])
        if statusCode != 0:
            status = FronstorStatus.ERROR
            message = self.get_deep_attribute(json, ['Head', 'Status', 'Reason'])
            message2 = self.get_deep_attribute(json, ['Head', 'Status', 'UserMessage'])
            print("extract failure: status = {}; message = {} ({})".format(status, message, message2))

        else:
            try:
                print("find_temp_and_cycle")
                values = self.find_temp_and_cycle(json)
                status = FronstorStatus.SUCCESS

            except AttributeError as e:
                status = FronstorStatus.ERROR
                message = 'exception: cannot extract temps and cycles!'
                print(message)
                print(traceback.format_exc())

        values = {}
        self.store_value(values, FronstorConstants.ITEM_INV_TEMP, None)
        self.store_value(values, 'valPvBat4Cycle', None)

        Result = namedtuple('Result', ['status', 'message', 'values'])
        result = Result(status, message, values)
        return result

# --------------------------------------------------------------------