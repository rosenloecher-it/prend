import unittest
from app.sample_rule import SampleRule
from prend.process import Process


class MockRegisterRuleManager:
    def __init__(self):
        self.rule = None

    def register_rule(self, rule):
        self.rule = rule


class MockRegisterProcess(Process):
    def __init__(self):
        super().__init__()
        self._rule_manager = MockRegisterRuleManager()


class TestDispatcher(unittest.TestCase):

    def test_dummy(self):
        process = Process()

        out = process._print_and_return(1)
        self.assertEqual(out, 1)

        out = process._print_and_return(None)
        self.assertEqual(out, None)

    def test_init_locale(self):
        # mainly test no crash
        result = Process._init_locale('non_sense_dfdsfs')
        self.assertEqual(result, False)

        result = Process._init_locale('')
        self.assertEqual(result, True)

        result = Process._init_locale('  ')
        self.assertEqual(result, True)

        result = Process._init_locale(None)
        self.assertEqual(result, True)

        result = Process._init_locale('de_DE.UTF8  ')
        self.assertEqual(result, True)

    def test_register_rule_instance(self):
        process1 = MockRegisterProcess()
        self.assertEqual(process1._exit_code, None)
        self.assertEqual(process1._rule_manager.rule, None)
        rule = SampleRule()
        process1.register_rule_instance(rule)
        self.assertEqual(process1._exit_code, None)
        self.assertEqual(process1._rule_manager.rule, rule)

        process2 = MockRegisterProcess()
        process2.register_rule_instance(MockRegisterProcess())
        self.assertEqual(process2._exit_code, 1)
        self.assertEqual(process2._rule_manager.rule, None)

    def test_register_rule_path(self):
        process1 = MockRegisterProcess()
        self.assertEqual(process1._exit_code, None)
        self.assertEqual(process1._rule_manager.rule, None)
        path = SampleRule.__module__ + '.' + SampleRule.__name__
        process1.register_rule_path(path)
        self.assertEqual(process1._exit_code, None)
        self.assertTrue(isinstance(process1._rule_manager.rule, SampleRule))

        process2 = MockRegisterProcess()
        path = MockRegisterProcess.__module__ + '.' + MockRegisterProcess.__name__
        try:
            process2.register_rule_path(path)
            self.assertTrue(False)
        except Exception:
            self.assertEqual(process2._exit_code, 1)
            self.assertEqual(process2._rule_manager.rule, None)

        process3 = MockRegisterProcess()
        path = 'asdfdqfg.does.not.Exists!'
        try:
            process3.register_rule_path(path)
            self.assertTrue(False)
        except Exception:
            self.assertEqual(process3._exit_code, 1)
            self.assertEqual(process3._rule_manager.rule, None)


if __name__ == '__main__':
    unittest.main()
