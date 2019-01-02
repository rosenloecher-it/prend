import unittest
from app.fronmod.fronmod_constants import FronmodConstants
from app.fronmod.fronmod_processor import FronmodProcessor
from app.fronmod.fronmod_reader import FronmodReader, ModbusResultItem
from prend.channel import Channel, ChannelType
from prend.state import State, StateType
from test.app.fronmod.mock_fronmod_reader import MockFronmodReader
from test.prend.oh.mock_oh_gateway import MockOhGateway


class TestFronmodProcessor(unittest.TestCase):

    def test_convert_scale_factor(self):

        item = ModbusResultItem('test')

        item.value = -2
        out = FronmodProcessor.convert_scale_factor(item.value)
        self.assertEqual(0.01, out)
        out = FronmodProcessor.convert_scale_factor(item)
        self.assertEqual(0.01, out)

        item.value = -1
        out = FronmodProcessor.convert_scale_factor(item.value)
        self.assertEqual(0.1, out)
        out = FronmodProcessor.convert_scale_factor(item)
        self.assertEqual(0.1, out)

        item.value = 0
        out = FronmodProcessor.convert_scale_factor(item.value)
        self.assertEqual(1, out)
        out = FronmodProcessor.convert_scale_factor(item)
        self.assertEqual(1, out)

        item.value = 1
        out = FronmodProcessor.convert_scale_factor(item.value)
        self.assertEqual(10, out)
        out = FronmodProcessor.convert_scale_factor(item)
        self.assertEqual(10, out)

        item.value = 2
        out = FronmodProcessor.convert_scale_factor(item.value)
        self.assertEqual(100, out)
        out = FronmodProcessor.convert_scale_factor(item)
        self.assertEqual(100, out)

        try:
            item.value = -11
            out = FronmodProcessor.convert_scale_factor(item)
            self.assertTrue(False)
        except ValueError:
            pass

        try:
            item.value = 11
            out = FronmodProcessor.convert_scale_factor(item)
            self.assertTrue(False)
        except ValueError:
            pass

        try:
            item.value = None
            out = FronmodProcessor.convert_scale_factor(item)
            self.assertTrue(False)
        except ValueError:
            pass

        try:
            out = FronmodProcessor.convert_scale_factor(None)
            self.assertTrue(False)
        except ValueError:
            pass


class TestFronmodProcessorProcessing(unittest.TestCase):

    def setUp(self):

        self.mock_gateway = MockOhGateway()
        self.mock_reader = MockFronmodReader()

        self.processor = FronmodProcessor()
        self.processor.set_oh_gateway(self.mock_gateway)
        self.processor.set_reader(self.mock_reader)

    def test_process_storage(self):

        channel = Channel.create_item(FronmodConstants.ITEM_BAT_FILL_STATE)
        state_in = State.create(StateType.DECIMAL, 99)
        self.mock_gateway.set_state(channel, state_in)

        self.mock_reader.set_mock_read(FronmodProcessor.FETCH_STORAGE, [
            124, 24, 3328, 100, 100, 0, 65535, 0, 300, 65535, 65535, 2, 10000, 10000, 65535, 65535, 65535, 1, 0, 0
            , 32768, 65534, 65534, 65534, 65534, 65534
        ])

        self.processor.process_storage()

        self.assertEqual(len(self.mock_gateway.sent_actions_list), 1)
        self.assertEqual(len(self.mock_gateway.sent_actions_dict), 1)
        state_comp = State.create(StateType.DECIMAL, 3)
        out = self.mock_gateway.exists_sent_item(channel, state_comp)


class TestFronmodProcessorReadRead(unittest.TestCase):
    pass

    # def print_read_result(self, desc, results):
    #     print(desc)
    #     if results is None:
    #         print('    None')
    #     else:
    #         for key, val in results.items():
    #             print('    {} = {}'.format(key, val))
    #
    # def test_read(self):
    #     reader = FronmodReader('192.168.12.42', 502)
    #     processor = FronmodProcessor()
    #     processor.set_reader(reader)
    #
    #     try:
    #         processor.open()
    #
    #         # results = processor.read_inverter_model()
    #         # self.print_read_result('read_inverter_model', results)
    #         #
    #         results = processor.read_storage_model()
    #         self.print_read_result('read_storage_model', results)
    #         #
    #         # results = processor.read_mppt_model()
    #         # self.print_read_result('read_mppt_model', results)
    #
    #         # results = processor.read_meter_model()
    #         # self.print_read_result('read_meter_model', results)
    #
    #         print('succeed')
    #     finally:
    #         processor.close()
    #
    #     self.assertTrue(True)

