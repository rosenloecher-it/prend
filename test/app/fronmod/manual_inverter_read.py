import unittest
from app.fronmod.fronmod_processor import FronmodProcessor
from app.fronmod.fronmod_reader import FronmodReader


# manual read inverter data


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

    # def test_print_read_result(self):
    #     self.print_read_result('test', None)

    def test_process_all(self):
        reader = FronmodReader(self.URL, self.PORT, print_registers=True)
        processor = FronmodProcessor()
        processor.set_reader(reader)

        try:
            processor.open()
            results = processor.process_inverter_model()
            self.print_read_result('process_inverter_model', results)

            processor.print_cached_values()

            results = processor.process_storage_model()
            self.print_read_result('process_storage_model', results)

            processor.print_cached_values()

            results = processor.process_meter_model()
            self.print_read_result('process_meter_model', results)

            processor.print_cached_values()

            results = processor.process_mppt_model()
            self.print_read_result('process_mppt_model', results)

            processor.print_cached_values()

            print('succeed')
            self.assertTrue(True)
        finally:
            processor.close()

    # def test_process_inverter_model(self):
    #     reader = FronmodReader(self.URL, self.PORT, print_registers=True)
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
    #     reader = FronmodReader(self.URL, self.PORT, print_registers=True)
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
    #     reader = FronmodReader(self.URL, self.PORT, print_registers=True)
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
    #     reader = FronmodReader(self.URL, self.PORT, print_registers=True)
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

