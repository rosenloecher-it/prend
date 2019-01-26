import unittest
import math
from app.fronmod.fronmod_config import FronmodConfig
from app.fronmod.fronmod_processor import FronmodProcessor
from app.fronmod.fronmod_reader import MobuResult, MobuFlag
from prend.state import State
from test.app.fronmod.mock_fronmod_reader import MockFronmodReader


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
            FronmodProcessor.convert_scale_factor(item)
            self.assertTrue(False)
        except ValueError:
            pass

        try:
            item.value = 11
            FronmodProcessor.convert_scale_factor(item)
            self.assertTrue(False)
        except ValueError:
            pass

        try:
            item.value = None
            FronmodProcessor.convert_scale_factor(item)
            self.assertTrue(False)
        except ValueError:
            pass

        try:
            FronmodProcessor.convert_scale_factor(None)
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
                result += MobuFlag.Q_QUICK
            if exp_medium != self.get_sent_count(MobuFlag.Q_MEDIUM):
                result += MobuFlag.Q_MEDIUM
            if exp_slow != self.get_sent_count(MobuFlag.Q_SLOW):
                result += MobuFlag.Q_SLOW
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

    def test_process_inverter_no_sun(self):

        self.mock_reader.set_mock_read(FronmodConfig.INVERTER_BATCH, [
            60, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 32704, 0, 32704, 0, 32704, 0,
            19157, 42320, 32704, 0, 32704, 0, 0, 0, 32704, 0, 32704, 0, 32704, 0, 32704, 0, 3, 3, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0
        ])

        self.processor.process_inverter_model()

        out = self.processor.check_sent_count(4, 4, 0)
        self.assertEqual(0, out)

        out = self.processor.exist_sent(MobuFlag.Q_MEDIUM, FronmodConfig.ITEM_INV_STATE_FRONIUS, 3)
        self.assertEqual(True, out)
        out = self.processor.exist_sent(MobuFlag.Q_MEDIUM, FronmodConfig.ITEM_INV_STATE_SUNSPEC, 3)
        self.assertEqual(True, out)
        out = self.processor.exist_sent(MobuFlag.Q_MEDIUM, FronmodConfig.ITEM_INV_AC_ENERGY_TOT, 7000744)
        self.assertEqual(True, out)
        out = self.processor.exist_sent(MobuFlag.Q_MEDIUM, FronmodConfig.SHOW_INV_AC_ENERGY_TOT, 7000.744)
        self.assertEqual(True, out)

        out = self.processor.exist_sent(MobuFlag.Q_QUICK, FronmodConfig.ITEM_INV_EFFICIENCY, 0)
        self.assertEqual(True, out)
        out = self.processor.exist_sent(MobuFlag.Q_QUICK, FronmodConfig.SHOW_INV_AC_POWER, 0)
        self.assertEqual(True, out)
        out = self.processor.exist_sent(MobuFlag.Q_QUICK, FronmodConfig.SHOW_INV_DC_POWER, 0)
        self.assertEqual(True, out)

        # FronmodProcessor.value_met_ac_power is None (set by "meter")
        out = self.processor.exist_sent(MobuFlag.Q_QUICK, FronmodConfig.ITEM_SELF_CONSUMPTION, None)
        self.assertEqual(True, out)

    def test_process_inverter_sun(self):

        self.mock_reader.set_mock_read(FronmodConfig.INVERTER_BATCH, [
            60, 16280, 20972, 16076, 52429, 16076, 52429, 16071, 44564, 17354, 45875, 17355, 39322, 17355, 58982, 17258,
            13107, 17258, 39322, 17259, 58982, 17293, 0, 16967, 55050, 17293, 58, 16256, 0, 49863, 65454, 19158, 29366,
            32704, 0, 32704, 0, 17310, 22938, 32704, 0, 32704, 0, 32704, 0, 32704, 0, 4, 4, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0
        ])

        self.processor.process_inverter_model()

        out = self.processor.check_sent_count(4, 4, 0)
        self.assertEqual(0, out)

        out = self.processor.exist_sent(MobuFlag.Q_MEDIUM, FronmodConfig.ITEM_INV_STATE_FRONIUS, 4)
        self.assertEqual(True, out)
        out = self.processor.exist_sent(MobuFlag.Q_MEDIUM, FronmodConfig.ITEM_INV_STATE_SUNSPEC, 4)
        self.assertEqual(True, out)
        out = self.processor.exist_sent(MobuFlag.Q_MEDIUM, FronmodConfig.ITEM_INV_AC_ENERGY_TOT, 7027035)
        self.assertEqual(True, out)
        out = self.processor.exist_sent(MobuFlag.Q_MEDIUM, FronmodConfig.SHOW_INV_AC_ENERGY_TOT, 7027.035)
        self.assertEqual(True, out)

        out = self.processor.exist_sent(MobuFlag.Q_QUICK, FronmodConfig.ITEM_INV_EFFICIENCY, 89.04325517223303)
        self.assertEqual(True, out)
        out = self.processor.exist_sent(MobuFlag.Q_QUICK, FronmodConfig.SHOW_INV_AC_POWER, 0.28200000000000003)
        self.assertEqual(True, out)
        out = self.processor.exist_sent(MobuFlag.Q_QUICK, FronmodConfig.SHOW_INV_DC_POWER, 0.31670001220703126)
        self.assertEqual(True, out)

        # FronmodProcessor.value_met_ac_power is None (set by "meter")
        out = self.processor.exist_sent(MobuFlag.Q_QUICK, FronmodConfig.ITEM_SELF_CONSUMPTION, None)
        self.assertEqual(True, out)

    def test_process_storage_empty3(self):

        self.mock_reader.set_mock_read(FronmodConfig.STORAGE_BATCH, [
            124, 24, 3328, 100, 100, 0, 65535, 0, 300, 65535, 65535, 2, 10000, 10000, 65535, 65535, 65535, 1, 0, 0
            , 32768, 65534, 65534, 65534, 65534, 65534
        ])

        self.processor.process_storage_model()

        out = self.processor.check_sent_count(2, 0, 0)
        self.assertEqual(0, out)

        out = self.processor.exist_sent(MobuFlag.Q_QUICK, FronmodConfig.ITEM_BAT_FILL_STATE, 3)
        self.assertEqual(True, out)

        out = self.processor.exist_sent(MobuFlag.Q_QUICK, FronmodConfig.ITEM_BAT_STATE, 2)
        self.assertEqual(True, out)

    def test_process_storage_discharge(self):

        self.mock_reader.set_mock_read(FronmodConfig.STORAGE_BATCH, [
            124, 24, 3328, 100, 100, 0, 65535, 0, 2400, 65535, 65535, 3, 10000, 10000, 65535, 65535, 65535, 1, 0, 0,
            32768, 65534, 65534, 65534, 65534, 65534
        ])

        self.processor.process_storage_model()

        out = self.processor.check_sent_count(2, 0, 0)
        self.assertEqual(0, out)

        out = self.processor.exist_sent(MobuFlag.Q_QUICK, FronmodConfig.ITEM_BAT_FILL_STATE, 24)
        self.assertEqual(True, out)

        out = self.processor.exist_sent(MobuFlag.Q_QUICK, FronmodConfig.ITEM_BAT_STATE, 3)
        self.assertEqual(True, out)

    def test_process_storage_loading(self):

        # todo: wrong state from inverter

        # self.mock_reader.set_mock_read(FronmodConfig.STORAGE_BATCH, [
        #     124, 24, 3328, 100, 100, 0, 65535, 0, 1100, 65535, 65535, 2, 10000, 10000, 65535, 65535, 65535, 1, 0, 0,
        #     32768, 65534, 65534, 65534, 65534, 65534
        # ])
        #
        # self.processor.process_storage_model()
        #
        # out = self.processor.check_sent_count(0, 2, 0)
        # self.assertEqual(0, out)
        #
        # out = self.processor.exist_sent(MobuFlag.Q_MEDIUM, FronmodConfig.ITEM_BAT_FILL_STATE, 11)
        # self.assertEqual(True, out)
        #
        # out = self.processor.exist_sent(MobuFlag.Q_MEDIUM, FronmodConfig.ITEM_BAT_STATE, 2)
        # self.assertEqual(True, out)
        pass

    def test_process_storage_holding(self):
        self.mock_reader.set_mock_read(FronmodConfig.STORAGE_BATCH, [
            124, 24, 3328, 100, 100, 0, 65535, 0, 2900, 65535, 65535, 6, 10000, 10000, 65535, 65535, 65535, 1, 0, 0,
            32768, 65534, 65534, 65534, 65534, 65534
        ])

        self.processor.process_storage_model()

        out = self.processor.check_sent_count(2, 0, 0)
        self.assertEqual(0, out)

        out = self.processor.exist_sent(MobuFlag.Q_QUICK, FronmodConfig.ITEM_BAT_FILL_STATE, 29)
        self.assertEqual(True, out)

        out = self.processor.exist_sent(MobuFlag.Q_QUICK, FronmodConfig.ITEM_BAT_STATE, 6)
        self.assertEqual(True, out)

    def test_process_mppt(self):

        self.mock_reader.set_mock_read(FronmodConfig.MPPT_BATCH, [
            160, 48, 65534, 65534, 65534, 32768, 0, 0, 2, 65535, 1, 21364, 29289, 28263, 8241, 0, 0, 0, 0, 55, 56620,
            31141, 0, 0, 9155, 20421, 32768, 4, 65535, 65535, 2, 21364, 29289, 28263, 8242, 0, 0, 0, 0, 2, 18320, 366,
            0, 0, 9155, 20421, 32768, 4
        ])

        bat_power_expected = -0.00366
        mod_power_expected = 0.31141

        self.processor.value_inv_dc_power = (mod_power_expected + bat_power_expected) * 1000

        self.processor.process_mppt_model()

        out = self.processor.check_sent_count(3, 2, 0)
        self.assertEqual(0, out)

        out = self.processor.exist_sent(MobuFlag.Q_MEDIUM, FronmodConfig.ITEM_MPPT_MOD_STATE, 4)
        self.assertEqual(True, out)
        out = self.processor.exist_sent(MobuFlag.Q_MEDIUM, FronmodConfig.ITEM_MPPT_BAT_STATE, 4)
        self.assertEqual(True, out)

        out = self.processor.exist_sent(MobuFlag.Q_QUICK, FronmodConfig.ITEM_MPPT_MOD_VOLTAGE, 566.2)
        self.assertEqual(True, out)
        out = self.processor.exist_sent(MobuFlag.Q_QUICK, FronmodConfig.SHOW_MPPT_BAT_POWER, bat_power_expected)
        self.assertEqual(True, out)
        out = self.processor.exist_sent(MobuFlag.Q_QUICK, FronmodConfig.SHOW_MPPT_MOD_POWER, mod_power_expected)
        self.assertEqual(True, out)

    def test_process_mppt_ffff_equals_0(self):
        # fronius delivers 0xffff for *MPPT_MOD_STATE + MPPT_BAT_POWER !!!

        self.mock_reader.set_mock_read(FronmodConfig.MPPT_BATCH, [
            160, 48, 65534, 65534, 65534, 32768, 0, 0, 2, 65535, 1, 21364, 29289, 28263, 8241, 0, 0, 0, 0, 0, 350,
            65535, 0, 0, 9161, 6067, 32768, 3, 65535, 65535, 2, 21364, 29289, 28263, 8242, 0, 0, 0, 0, 0, 260, 0, 0, 0,
            9161, 6067, 32768, 3
        ])

        self.processor.process_mppt_model()

        out = self.processor.check_sent_count(3, 2, 0)
        self.assertEqual(0, out)

        out = self.processor.exist_sent(MobuFlag.Q_MEDIUM, FronmodConfig.ITEM_MPPT_MOD_STATE, 3)
        self.assertEqual(True, out)
        out = self.processor.exist_sent(MobuFlag.Q_MEDIUM, FronmodConfig.ITEM_MPPT_BAT_STATE, 3)
        self.assertEqual(True, out)

        out = self.processor.exist_sent(MobuFlag.Q_QUICK, FronmodConfig.ITEM_MPPT_MOD_VOLTAGE, 3.5)
        self.assertEqual(True, out)
        out = self.processor.exist_sent(MobuFlag.Q_QUICK, FronmodConfig.SHOW_MPPT_BAT_POWER, 0.0)
        self.assertEqual(True, out)
        out = self.processor.exist_sent(MobuFlag.Q_QUICK, FronmodConfig.SHOW_MPPT_MOD_POWER, 0.0)
        self.assertEqual(True, out)

    def test_mppt_storage_ffff_equals_0(self):
        # fronius delivers 0xffff for *MPPT_MOD_STATE + MPPT_BAT_POWER !!!

        self.mock_reader.set_mock_read(FronmodConfig.MPPT_BATCH, [
            160, 48, 65534, 65534, 65534, 32768, 0, 0, 2, 65535, 1, 21364, 29289, 28263, 8241, 0, 0, 0, 0, 0, 350,
            65535, 0, 0, 9161, 6067, 32768, 3, 65535, 65535, 2, 21364, 29289, 28263, 8242, 0, 0, 0, 0, 0, 260, 0, 0, 0,
            9161, 6067, 32768, 3
        ])

        self.processor.process_mppt_model()

        out = self.processor.check_sent_count(3, 2, 0)
        self.assertEqual(0, out)

        out = self.processor.exist_sent(MobuFlag.Q_MEDIUM, FronmodConfig.ITEM_MPPT_MOD_STATE, 3)
        self.assertEqual(True, out)
        out = self.processor.exist_sent(MobuFlag.Q_MEDIUM, FronmodConfig.ITEM_MPPT_BAT_STATE, 3)
        self.assertEqual(True, out)

        out = self.processor.exist_sent(MobuFlag.Q_QUICK, FronmodConfig.ITEM_MPPT_MOD_VOLTAGE, 3.5)
        self.assertEqual(True, out)
        out = self.processor.exist_sent(MobuFlag.Q_QUICK, FronmodConfig.SHOW_MPPT_BAT_POWER, 0.0)
        self.assertEqual(True, out)
        out = self.processor.exist_sent(MobuFlag.Q_QUICK, FronmodConfig.SHOW_MPPT_MOD_POWER, 0.0)
        self.assertEqual(True, out)

    def test_process_meter(self):

        self.mock_reader.set_mock_read(FronmodConfig.METER_BATCH, [
            16384, 16968, 0, 16528, 62915, 16967, 55050, 16831, 2621, 49802, 40632, 17298, 61932, 17197, 16187, 17236,
            42362, 17172, 54788, 50066, 61932, 49840, 57672, 49929, 53084, 49799, 18350, 15395, 55050, 16122, 57672,
            15918, 5243, 48949, 49807, 19079, 34320, 32704, 0, 32704, 0, 32704, 0, 18772, 13440, 32704, 0, 32704, 0,
            32704
        ])

        self.processor.process_meter_model()

        out = self.processor.check_sent_count(2, 5, 0)
        self.assertEqual(0, out)

        out = self.processor.exist_sent(MobuFlag.Q_MEDIUM, FronmodConfig.ITEM_MET_AC_FREQUENCY, 50.0)
        self.assertEqual(True, out)

        out = self.processor.exist_sent(MobuFlag.Q_MEDIUM, FronmodConfig.ITEM_MET_ENERGY_EXP_TOT, 4440840.0)
        self.assertEqual(True, out)
        out = self.processor.exist_sent(MobuFlag.Q_MEDIUM, FronmodConfig.SHOW_MET_ENERGY_EXP_TOT, 4440.84)
        self.assertEqual(True, out)

        out = self.processor.exist_sent(MobuFlag.Q_MEDIUM, FronmodConfig.ITEM_MET_ENERGY_IMP_TOT, 869192.0)
        self.assertEqual(True, out)
        out = self.processor.exist_sent(MobuFlag.Q_MEDIUM, FronmodConfig.SHOW_MET_ENERGY_IMP_TOT, 869.192)
        self.assertEqual(True, out)

        out = self.processor.exist_sent(MobuFlag.Q_QUICK, FronmodConfig.SHOW_MET_AC_POWER, 0.00453000020980835)
        self.assertEqual(True, out)

        out = self.processor.exist_sent(MobuFlag.Q_QUICK, FronmodConfig.ITEM_SELF_CONSUMPTION, None)
        self.assertEqual(True, out)

    def test_process_self_consumption(self):

        self.mock_reader.set_mock_read(FronmodConfig.INVERTER_BATCH, [
            60, 16744, 52429, 16539, 34079, 16539, 34079, 16538, 36700, 17355, 52429, 17357, 39322, 17357, 52429, 17258,
            45875, 17261, 26214, 17262, 13107, 17751, 36864, 16967, 62915, 17751, 37126, 49576, 0, 17095, 65293, 19158,
            64272, 32704, 0, 32704, 0, 17759, 57344, 32704, 0, 32704, 0, 32704, 0, 32704, 0, 4, 4, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0
        ])

        self.processor.process_inverter_model()

        self.mock_reader.set_mock_read(FronmodConfig.METER_BATCH, [
            3277, 16968, 0, 50336, 573, 17489, 164, 50308, 49889, 50307, 49070, 17571, 49152, 17494, 1720, 17543, 25876,
            17540, 39715, 50059, 12124, 49841, 47186, 49936, 28180, 49716, 20972, 49016, 20972, 16253, 28836, 49021,
            28836, 49021, 28836, 19079, 35284, 32704, 0, 32704, 0, 32704, 0, 18772, 13440, 32704, 0, 32704, 0, 32704
        ])

        self.processor.process_meter_model()

        out = self.processor.check_sent_count(5, 9, 0)
        self.assertEqual(0, out)

        out = self.processor.exist_sent(MobuFlag.Q_QUICK, FronmodConfig.SHOW_MET_AC_POWER, -1.2800699462890626)
        self.assertEqual(True, out)

        out = self.processor.exist_sent(MobuFlag.Q_QUICK, FronmodConfig.ITEM_SELF_CONSUMPTION, -2.1689300537109375)
        self.assertEqual(True, out)

    def test_error_reset_items(self):

        self.mock_reader.clear_mock_reads()  # has to fail => ValueError by MockReader

        try:
            self.processor.process_meter_model()
            self.assertEqual(True, False)
        except Exception as ex:
            print('exception: ', ex)
            pass

        out = self.processor.check_sent_count(2, 5, 0)
        self.assertEqual(0, out)

        out = self.processor.exist_sent(MobuFlag.Q_MEDIUM, FronmodConfig.ITEM_MET_AC_FREQUENCY, None)
        self.assertEqual(True, out)

        out = self.processor.exist_sent(MobuFlag.Q_MEDIUM, FronmodConfig.ITEM_MET_ENERGY_EXP_TOT, None)
        self.assertEqual(True, out)
        out = self.processor.exist_sent(MobuFlag.Q_MEDIUM, FronmodConfig.SHOW_MET_ENERGY_EXP_TOT, None)
        self.assertEqual(True, out)

        out = self.processor.exist_sent(MobuFlag.Q_MEDIUM, FronmodConfig.ITEM_MET_ENERGY_IMP_TOT, None)
        self.assertEqual(True, out)
        out = self.processor.exist_sent(MobuFlag.Q_MEDIUM, FronmodConfig.SHOW_MET_ENERGY_IMP_TOT, None)
        self.assertEqual(True, out)

        out = self.processor.exist_sent(MobuFlag.Q_QUICK, FronmodConfig.SHOW_MET_AC_POWER, None)
        self.assertEqual(True, out)

        out = self.processor.exist_sent(MobuFlag.Q_QUICK, FronmodConfig.ITEM_SELF_CONSUMPTION, None)
        self.assertEqual(True, out)

        send_list = self.processor.get_send_data(MobuFlag.Q_QUICK)
        self.assertEqual(2, len(send_list))
        # reseted !?
        send_list = self.processor.get_send_data(MobuFlag.Q_QUICK)
        self.assertEqual(0, len(send_list))

        # eflow should/must be 0!!!
        send_list = self.processor.get_send_data(MobuFlag.Q_MEDIUM)
        self.assertEqual(5, len(send_list))
        # reseted !?
        send_list = self.processor.get_send_data(MobuFlag.Q_MEDIUM)
        self.assertEqual(0, len(send_list))
