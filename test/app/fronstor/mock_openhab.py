import copy
from app.openhab import BaseOpenhab


class MockOpenhab(BaseOpenhab):

    def __init__(self):
        self.values = {}

    def open(self):
        pass


    def close(self):
        pass


    def load_values(self):
        pass


    def send_value(self, channel, value):
        print('send_value({}): {}'.format(channel, value))

    def is_battery_active(self):
        return True

