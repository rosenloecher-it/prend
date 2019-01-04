import unittest
from app.fronmod.fronmod_constants import FronmodConstants
from app.fronmod.fronmod_processor import FronmodProcessor
from app.fronmod.fronmod_reader import FronmodReader, MobuResult
from prend.channel import Channel, ChannelType
from prend.state import State, StateType
from test.app.fronmod.mock_fronmod_reader import MockFronmodReader
from test.prend.oh.mock_oh_gateway import MockOhGateway


class TestFronmodProcessor(unittest.TestCase):

    def test_convert_scale_factor(self):

        item = MobuResult('test')

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

    def test_process_inverter(self):
        def_state_type = StateType.DECIMAL
        read_conf = FronmodProcessor.FETCH_INVERTER
        for item in read_conf.items:
            channel = Channel.create_item(item.name)
            state_in = State.create(def_state_type, None)
            self.mock_gateway.set_state(channel, state_in)

        self.mock_reader.set_mock_read(read_conf, [
            60, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 32704, 0, 32704, 0, 32704, 0,
            19157, 42320, 32704, 0, 32704, 0, 0, 0, 32704, 0, 32704, 0, 32704, 0, 32704, 0, 3, 3, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0
        ])

        self.processor.process_inverter_model()

        self.assertEqual(len(self.mock_gateway.sent_actions_list), len(read_conf.items))
        self.assertEqual(len(self.mock_gateway.sent_actions_dict), len(read_conf.items))

        # todo state_comp = State.create(def_state_type, 7000.744)
        state_comp = State.create(def_state_type, 7000744)
        out = self.mock_gateway.exists_sent_item(FronmodConstants.ITEM_INV_AC_ENERGY_TOT, state_comp)
        self.assertEqual(True, out)

        out = self.mock_gateway.exists_sent_item(FronmodConstants.ITEM_INV_AC_POWER, 0.0)
        self.assertEqual(True, out)

        out = self.mock_gateway.exists_sent_item(FronmodConstants.ITEM_INV_DC_POWER, 0.0)
        self.assertEqual(True, out)

        state_comp = State.create(def_state_type, 1.1)
        out = self.mock_gateway.exists_sent_item(FronmodConstants.ITEM_INV_STATE_FRONIUS, 3)
        self.assertEqual(True, out)

        out = self.mock_gateway.exists_sent_item(FronmodConstants.ITEM_INV_STATE_SUNSPEC, 3)
        self.assertEqual(True, out)


    def test_process_storage(self):

        channel = Channel.create_item(FronmodConstants.ITEM_BAT_FILL_STATE)
        state_in = State.create(StateType.DECIMAL, 99)
        self.mock_gateway.set_state(channel, state_in)

        self.mock_reader.set_mock_read(FronmodProcessor.FETCH_STORAGE, [
            124, 24, 3328, 100, 100, 0, 65535, 0, 300, 65535, 65535, 2, 10000, 10000, 65535, 65535, 65535, 1, 0, 0
            , 32768, 65534, 65534, 65534, 65534, 65534
        ])

        self.processor.process_storage_model()

        self.assertEqual(len(self.mock_gateway.sent_actions_list), 1)
        self.assertEqual(len(self.mock_gateway.sent_actions_dict), 1)
        state_comp = State.create(StateType.DECIMAL, 3)
        out = self.mock_gateway.exists_sent_item(channel, state_comp)
        self.assertEqual(True, out)

    def test_mppt_storage(self):

        channel = Channel.create_item(FronmodConstants.ITEM_BAT_FILL_STATE)
        # state_in = State.create(StateType.DECIMAL, 99)
        # self.mock_gateway.set_state(channel, state_in)
        #
        # self.mock_reader.set_mock_read(FronmodProcessor.FETCH_STORAGE, [
        #     124, 24, 3328, 100, 100, 0, 65535, 0, 300, 65535, 65535, 2, 10000, 10000, 65535, 65535, 65535, 1, 0, 0
        #     , 32768, 65534, 65534, 65534, 65534, 65534
        # ])
        #
        # self.processor.process_storage_model()
        #
        # self.assertEqual(len(self.mock_gateway.sent_actions_list), 1)
        # self.assertEqual(len(self.mock_gateway.sent_actions_dict), 1)
        # state_comp = State.create(StateType.DECIMAL, 3)
        # out = self.mock_gateway.exists_sent_item(channel, state_comp)
        # self.assertEqual(True, out)

    def test_process_meter(self):
        def_state_type = StateType.DECIMAL
        read_conf = FronmodProcessor.FETCH_METER
        for item in read_conf.items:
            channel = Channel.create_item(item.name)
            state_in = State.create(def_state_type, None)
            self.mock_gateway.set_state(channel, state_in)

        self.mock_reader.set_mock_read(FronmodProcessor.FETCH_METER, [
            124, 16440, 62915, 16249, 39322, 16208, 41943, 16268, 52429, 17259, 56798, 17259, 13107, 17259, 58982,
            17260, 32768, 17356, 17476, 17356, 0, 17356, 36045, 17356, 16384, 16968, 0, 17402, 33096, 17195, 57672,
            17073, 51118, 17264, 15729, 17428, 16384, 17253, 20972, 17216, 16941, 17282, 4915, 50079, 11469, 49888,
            11796, 49931, 64881, 49796, 35389, 16215, 2621, 16212, 31457, 16135, 44564, 16245, 49807, 19079, 16250,
            32704, 0, 32704, 0, 32704, 0, 18754, 62816, 32704, 0, 32704, 0, 32704, 0, 32704, 0, 32704, 0, 32704, 0,
            32704, 0, 32704, 0, 32704, 0, 32704, 0, 32704, 0, 32704, 0, 32704, 0, 32704, 0, 32704, 0, 32704, 0, 32704,
            0, 32704, 0, 32704, 0, 32704, 0, 32704, 0, 32704, 0, 32704, 0, 32704, 0, 32704, 0, 32704, 0, 32704, 0, 0
        ])

        self.processor.process_meter_model()

        self.assertEqual(len(self.mock_gateway.sent_actions_list), len(read_conf.items))
        self.assertEqual(len(self.mock_gateway.sent_actions_dict), len(read_conf.items))

        # ITEM_MET_AC_FREQUENCY = 'valPvMetAcFrequency'
        # ITEM_MET_AC_POWER = 'valPvMetAcPower'
        # ITEM_MET_ENERGY_EXP_TOT = 'valPvMetEnergyExpTot'
        # ITEM_MET_ENERGY_IMP_TOT = 'valPvMetEnergyImpTot'

        out = self.mock_gateway.exists_sent_item(FronmodConstants.ITEM_MET_AC_FREQUENCY, 50.0)
        self.assertEqual(True, out)

        out = self.mock_gateway.exists_sent_item(FronmodConstants.ITEM_MET_AC_POWER, 501.010009765625)
        self.assertEqual(True, out)

        state_comp = State.create(def_state_type, 1.1)
        out = self.mock_gateway.exists_sent_item(FronmodConstants.ITEM_MET_ENERGY_EXP_TOT, 4431805.0)
        self.assertEqual(True, out)

        out = self.mock_gateway.exists_sent_item(FronmodConstants.ITEM_MET_ENERGY_IMP_TOT, 798550.0)
        self.assertEqual(True, out)

class TestFronmodProcessorReadReal(unittest.TestCase):

    URL = '192.168.12.42'
    PORT = 502

    # def print_read_result(self, desc, results):
    #     print(desc)
    #     if results is None:
    #         print('    None')
    #     else:
    #         for key, val in results.items():
    #             print('    {} = {}'.format(key, val))
    #
    # def test_process_inverter_model(self):
    #     reader = FronmodReader(self.URL, self.PORT)
    #     processor = FronmodProcessor()
    #     processor.set_reader(reader)
    #
    #     try:
    #         processor.open()
    #         results = processor.process_inverter_model()
    #         self.print_read_result('process_inverter_model', results)
    #
    #         print('succeed')
    #         self.assertTrue(True)
    #     finally:
    #         processor.close()
    #
    # def test_process_storage_model(self):
    #     reader = FronmodReader(self.URL, self.PORT)
    #     processor = FronmodProcessor()
    #     processor.set_reader(reader)
    #
    #     try:
    #         processor.open()
    #         results = processor.process_storage_model()
    #         self.print_read_result('process_storage_model', results)
    #
    #         print('succeed')
    #         self.assertTrue(True)
    #     finally:
    #         processor.close()
    #
    # def test_process_mppt_model(self):
    #     reader = FronmodReader(self.URL, self.PORT)
    #     processor = FronmodProcessor()
    #     processor.set_reader(reader)
    #
    #     try:
    #         processor.open()
    #         results = processor.process_mppt_model()
    #         self.print_read_result('process_mppt_model', results)
    #
    #         print('succeed')
    #         self.assertTrue(True)
    #     finally:
    #         processor.close()
    #
    # def test_process_meter_model(self):
    #     reader = FronmodReader(self.URL, self.PORT)
    #     processor = FronmodProcessor()
    #     processor.set_reader(reader)
    #
    #     try:
    #         processor.open()
    #         results = processor.process_meter_model()
    #         self.print_read_result('process_meter_model', results)
    #
    #         print('succeed')
    #         self.assertTrue(True)
    #     finally:
    #         processor.close()


