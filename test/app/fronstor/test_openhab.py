import unittest
from app.openhab import Openhab
from app.constants import Constants


class TestOpenhab(unittest.TestCase):

    def print_channel(self, openhab, channel):
        print("{}: {}".format(channel, openhab.get_value(channel)))

    def test_loadValues(self):
        with Openhab(Constants.url_openhab) as openhab:
            openhab.open()
            openhab.clear()
            openhab.load_values()
            is_battery_active = openhab.is_battery_active()
            print('is_battery_active =', is_battery_active)


            self.print_channel(openhab, Constants.item_inv_temp)
            self.print_channel(openhab, Constants.item_bat_temp_max)

            for i in range(0, Constants.item_bat_count):
                self.print_channel(openhab, Constants.item_bat_temp_format.format(i + 1))

            for i in range(0, Constants.item_bat_count):
                self.print_channel(openhab, Constants.item_bat_cycle_format.format(i + 1))

            self.print_channel(openhab, Constants.item_bat_cycle_span)


if __name__ == '__main__':
    unittest.main()