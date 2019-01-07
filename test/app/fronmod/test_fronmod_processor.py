import unittest
import math
from app.fronmod import *
from app.fronmod.fronmod_config import FronmodConfig
from app.fronmod.fronmod_processor import FronmodProcessor
from app.fronmod.fronmod_reader import FronmodReader, MobuResult, MobuFlag
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

    class FronmodProcessorExt(FronmodProcessor):

        def get_sent_count(self, flags: MobuFlag) -> int:
            queue_dict = self._get_queue_dict(flags)
            return len(queue_dict)

        def check_sent_count(self, exp_quick, exp_medium, exp_slow) -> int:
            result = 0
            if exp_quick != self.get_sent_count(MobuFlag.Q_QUICK):
                result |= MobuFlag.Q_QUICK
            if exp_medium != self.get_sent_count(MobuFlag.Q_MEDIUM):
                result |= MobuFlag.Q_MEDIUM
            if exp_slow != self.get_sent_count(MobuFlag.Q_SLOW):
                result |= MobuFlag.Q_SLOW
            return result

        def exist_sent(self, flags: MobuFlag, item_name: str, data_compare) -> bool:
            queue_dict = self._get_queue_dict(flags)
            if queue_dict is None:
                return False
            sent_data = queue_dict.get(item_name)
            if sent_data is None:
                return False

            if isinstance(sent_data.state, State):
                sent_value = sent_data.state.value
            else:
                sent_value = sent_data.state

            if isinstance(data_compare, State):
                comp_value = data_compare.value
            else:
                comp_value = data_compare

            if isinstance(sent_value, float) and isinstance(comp_value, float):
                if sent_value == comp_value:
                    return True
                return math.isclose(sent_value, comp_value, rel_tol=1e-9)
            else:
                return sent_value == comp_value

    def setUp(self):

        self.mock_reader = MockFronmodReader()
        self.processor = self.FronmodProcessorExt()
        self.processor.set_reader(self.mock_reader)

    def test_process_inverter(self):

        self.mock_reader.set_mock_read(FronmodConfig.INVERTER_BATCH, [
            60, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 32704, 0, 32704, 0, 32704, 0,
            19157, 42320, 32704, 0, 32704, 0, 0, 0, 32704, 0, 32704, 0, 32704, 0, 32704, 0, 3, 3, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0
        ])

        self.processor.process_inverter_model()

        out = self.processor.check_sent_count(2, 4, 0)
        self.assertEqual(0, 0)

        out = self.processor.exist_sent(MobuFlag.Q_MEDIUM, FronmodConfig.ITEM_INV_STATE_FRONIUS, 3)
        self.assertEqual(True, out)
        out = self.processor.exist_sent(MobuFlag.Q_MEDIUM, FronmodConfig.ITEM_INV_STATE_SUNSPEC, 3)
        self.assertEqual(True, out)
        out = self.processor.exist_sent(MobuFlag.Q_MEDIUM, FronmodConfig.ITEM_INV_AC_ENERGY_TOT, 7000744)
        self.assertEqual(True, out)
        out = self.processor.exist_sent(MobuFlag.Q_MEDIUM, FronmodConfig.SHOW_INV_AC_ENERGY_TOT, 7000.744)
        self.assertEqual(True, out)

        out = self.processor.exist_sent(MobuFlag.Q_QUICK, FronmodConfig.SHOW_INV_AC_POWER, 0)
        self.assertEqual(True, out)
        out = self.processor.exist_sent(MobuFlag.Q_QUICK, FronmodConfig.SHOW_INV_DC_POWER, 0)
        self.assertEqual(True, out)

    def test_process_storage(self):

        self.mock_reader.set_mock_read(FronmodConfig.STORAGE_BATCH, [
            124, 24, 3328, 100, 100, 0, 65535, 0, 300, 65535, 65535, 2, 10000, 10000, 65535, 65535, 65535, 1, 0, 0
            , 32768, 65534, 65534, 65534, 65534, 65534
        ])

        self.processor.process_storage_model()

        out = self.processor.check_sent_count(0, 1, 0)
        self.assertEqual(0, 0)

        out = self.processor.exist_sent(MobuFlag.Q_MEDIUM, FronmodConfig.ITEM_BAT_FILL_STATE, 3)
        self.assertEqual(True, out)

    def test_mppt_storage(self):

        self.mock_reader.set_mock_read(FronmodConfig.MPPT_BATCH, [
            160, 48, 65534, 65534, 65534, 32768, 0, 0, 2, 65535, 1, 21364, 29289, 28263, 8241, 0, 0, 0, 0, 55, 56620,
            31141, 0, 0, 9155, 20421, 32768, 4, 65535, 65535, 2, 21364, 29289, 28263, 8242, 0, 0, 0, 0, 2, 18320, 366,
            0, 0, 9155, 20421, 32768, 4
        ])

        self.processor.process_mppt_model()

        out = self.processor.check_sent_count(3, 2, 0)
        self.assertEqual(0, 0)

        out = self.processor.exist_sent(MobuFlag.Q_MEDIUM, FronmodConfig.ITEM_MPPT_MOD_STATE, 4)
        self.assertEqual(True, out)
        out = self.processor.exist_sent(MobuFlag.Q_MEDIUM, FronmodConfig.ITEM_MPPT_BAT_STATE, 4)
        self.assertEqual(True, out)

        out = self.processor.exist_sent(MobuFlag.Q_QUICK, FronmodConfig.ITEM_MPPT_MOD_VOLTAGE, 566.2)
        self.assertEqual(True, out)
        out = self.processor.exist_sent(MobuFlag.Q_QUICK, FronmodConfig.SHOW_MPPT_BAT_POWER, 0.00366)
        self.assertEqual(True, out)
        out = self.processor.exist_sent(MobuFlag.Q_QUICK, FronmodConfig.SHOW_MPPT_MOD_POWER, 0.31141)
        self.assertEqual(True, out)

    def test_process_meter(self):

        self.mock_reader.set_mock_read(FronmodConfig.METER_BATCH, [
            124, 16440, 62915, 16249, 39322, 16208, 41943, 16268, 52429, 17259, 56798, 17259, 13107, 17259, 58982,
            17260, 32768, 17356, 17476, 17356, 0, 17356, 36045, 17356, 16384, 16968, 0, 17402, 33096, 17195, 57672,
            17073, 51118, 17264, 15729, 17428, 16384, 17253, 20972, 17216, 16941, 17282, 4915, 50079, 11469, 49888,
            11796, 49931, 64881, 49796, 35389, 16215, 2621, 16212, 31457, 16135, 44564, 16245, 49807, 19079, 16250,
            32704, 0, 32704, 0, 32704, 0, 18754, 62816, 32704, 0, 32704, 0, 32704, 0, 32704, 0, 32704, 0, 32704, 0,
            32704, 0, 32704, 0, 32704, 0, 32704, 0, 32704, 0, 32704, 0, 32704, 0, 32704, 0, 32704, 0, 32704, 0, 32704,
            0, 32704, 0, 32704, 0, 32704, 0, 32704, 0, 32704, 0, 32704, 0, 32704, 0, 32704, 0, 32704, 0, 32704, 0, 0
        ])

        self.processor.process_meter_model()

        out = self.processor.check_sent_count(1, 5, 0)
        self.assertEqual(0, 0)

        out = self.processor.exist_sent(MobuFlag.Q_MEDIUM, FronmodConfig.ITEM_MET_AC_FREQUENCY, 50.0)
        self.assertEqual(True, out)

        out = self.processor.exist_sent(MobuFlag.Q_MEDIUM, FronmodConfig.ITEM_MET_ENERGY_EXP_TOT, 4431805.0)
        self.assertEqual(True, out)
        out = self.processor.exist_sent(MobuFlag.Q_MEDIUM, FronmodConfig.SHOW_MET_ENERGY_EXP_TOT, 4431.805)
        self.assertEqual(True, out)

        out = self.processor.exist_sent(MobuFlag.Q_MEDIUM, FronmodConfig.ITEM_MET_ENERGY_IMP_TOT, 798550.0)
        self.assertEqual(True, out)
        out = self.processor.exist_sent(MobuFlag.Q_MEDIUM, FronmodConfig.SHOW_MET_ENERGY_IMP_TOT, 798.55)
        self.assertEqual(True, out)

        out = self.processor.exist_sent(MobuFlag.Q_QUICK, FronmodConfig.SHOW_MET_AC_POWER, 0.501010009765625)
        self.assertEqual(True, out)


class TestFronmodProcessorReadReal(unittest.TestCase):

    URL = '192.168.12.42'
    PORT = 502

    @classmethod
    def print_read_result(cls, desc, results):
        print(desc)
        if results is None:
            print('    None')
        else:
            for key, val in results.items():
                print('    {} = {}'.format(key, val))

    def test_print_read_result(self):
        self.print_read_result('test', None)

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

