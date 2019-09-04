import unittest
from prend.config import ConfigLoader
from prend.rule import Rule


class MockRule(Rule):

    def __init__(self):
        super().__init__()
        self._config = {}

    def register_actions(self) -> None:
        pass

    def notify_action(self, action) -> None:
        pass

    def add_to_config(self, section_name, value_name, value):
        ConfigLoader.add_to_rule_config(self._config, section_name, value_name, str(value))


class TestRule(unittest.TestCase):

    def test_get_config(self):

        rule = MockRule()
        section_name = 'section'

        value_name = 'bool'
        rule.add_to_config(section_name, value_name, ' trUe ')
        out = rule.get_config_bool(section_name, value_name)
        self.assertEqual(out, True)

        rule.add_to_config(section_name, value_name, '   ')
        out = rule.get_config_bool(section_name, value_name, True)
        self.assertEqual(out, True)

        out = rule.get_config_bool('section_should_not_exists', value_name, True)
        self.assertEqual(out, True)

        value_name = 'int'
        rule.add_to_config(section_name, value_name, '  123 ')
        out = rule.get_config_int(section_name, value_name)
        self.assertEqual(out, 123)

        rule.add_to_config(section_name, value_name, '  -23 ')
        out = rule.get_config_int(section_name, value_name)
        self.assertEqual(out, -23)

        rule.add_to_config(section_name, value_name, None)
        out = rule.get_config_int(section_name, value_name, -23)
        self.assertEqual(out, -23)

        out = rule.get_config_int('section_should_not_exists', value_name, 123)
        self.assertEqual(out, 123)

        value_name = 'float'
        rule.add_to_config(section_name, value_name, '  123.12 ')
        out = rule.get_config_float(section_name, value_name)
        self.assertEqual(out, 123.12)

        rule.add_to_config(section_name, value_name, '  999 ')
        out = rule.get_config_float(section_name, value_name)
        self.assertEqual(out, 999)

        rule.add_to_config(section_name, value_name, '  -23.9 ')
        out = rule.get_config_float(section_name, value_name)
        self.assertEqual(out, -23.9)

        rule.add_to_config(section_name, value_name, None)
        out = rule.get_config_float(section_name, value_name, -23.6)
        self.assertEqual(out, -23.6)

        out = rule.get_config_float('section_should_not_exists', value_name, 123.5)
        self.assertEqual(out, 123.5)

        out = rule.get_config_float('section_should_not_exists', value_name, 123)
        self.assertEqual(out, 123)


if __name__ == '__main__':
    unittest.main()
