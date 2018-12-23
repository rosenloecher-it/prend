import copy
import unittest
from app.led_status_rule import LedStatusRule, EvalItem, EvalType, EvalState
from prend.action import Action
from prend.channel import Channel
from prend.state import State, StateType
from prend.values import OnOffValue, OpeningValue


class SentEvalState:
    def __init__(self, led_item, eval_set, check_diff_and_update):
        self.led_item = led_item
        self.eval_set = eval_set
        self.check_diff_and_update = check_diff_and_update

    def __repr__(self) -> str:
        return '{}(led={}, {}, upd={})'.format(
            self.__class__.__name__,
            self.led_item,
            self.eval_set,
            self.check_diff_and_update)


class MockLedStatusRule(LedStatusRule):

    def __init__(self):
        super().__init__()

        self.dummy_states = {}
        self.sent_list = []

    def is_connected(self):
        return True

    def clear(self):
        self.dummy_states.clear()

    def get_states(self) -> dict:
        return copy.deepcopy(self.dummy_states)

    def get_state(self, channel):
        state_out = None
        if channel:
            state = self.dummy_states.get(channel)
            if state:
                state_out = copy.deepcopy(state)
        return state_out

    def set_item_state(self, channel_name, state_in):
        channel = Channel.create_item(channel_name)
        if state_in is not None:
            state = copy.deepcopy(state_in)
        else:
            state = None
        self.dummy_states[channel] = state

    def _send_eval_state(self, led_item, eval_set, check_diff_and_update=False):
        sent_data = SentEvalState(led_item, eval_set, check_diff_and_update)
        self.sent_list.append(sent_data)


class TestLedStatusRule(unittest.TestCase):

    def test_check_eval_item_window(self):

        rule = MockLedStatusRule()
        item_name = 'window'

        # window. 0 and 1

        rule.set_item_state(item_name, State.create(StateType.DECIMAL, 0.0))
        eval_item = EvalItem(EvalType.OPEN, item_name)

        eval_state_out = rule._check_eval_item(eval_item, EvalState.GREEN)
        self.assertEqual(EvalState.GREEN, eval_state_out)
        eval_state_out = rule._check_eval_item(eval_item, EvalState.ORANGE)
        self.assertEqual(EvalState.ORANGE, eval_state_out)
        eval_state_out = rule._check_eval_item(eval_item, EvalState.RED)
        self.assertEqual(EvalState.RED, eval_state_out)

        rule.set_item_state(item_name, State.create(StateType.DECIMAL, 1.0))
        eval_item = EvalItem(EvalType.OPEN, item_name)

        eval_state_out = rule._check_eval_item(eval_item, EvalState.GREEN)
        self.assertEqual(EvalState.RED, eval_state_out)
        eval_state_out = rule._check_eval_item(eval_item, EvalState.ORANGE)
        self.assertEqual(EvalState.RED, eval_state_out)
        eval_state_out = rule._check_eval_item(eval_item, EvalState.RED)
        self.assertEqual(EvalState.RED, eval_state_out)

        # window: string - open, closed, tilted

        rule.set_item_state(item_name, State.create(StateType.STRING, OpeningValue.CLOSED.name))
        eval_item = EvalItem(EvalType.OPEN, item_name)

        eval_state_out = rule._check_eval_item(eval_item, EvalState.GREEN)
        self.assertEqual(EvalState.GREEN, eval_state_out)
        eval_state_out = rule._check_eval_item(eval_item, EvalState.ORANGE)
        self.assertEqual(EvalState.ORANGE, eval_state_out)
        eval_state_out = rule._check_eval_item(eval_item, EvalState.RED)
        self.assertEqual(EvalState.RED, eval_state_out)

        rule.set_item_state(item_name, State.create(StateType.STRING, OpeningValue.TILTED.name))
        eval_item = EvalItem(EvalType.OPEN, item_name)

        eval_state_out = rule._check_eval_item(eval_item, EvalState.GREEN)
        self.assertEqual(EvalState.ORANGE, eval_state_out)
        eval_state_out = rule._check_eval_item(eval_item, EvalState.ORANGE)
        self.assertEqual(EvalState.ORANGE, eval_state_out)
        eval_state_out = rule._check_eval_item(eval_item, EvalState.RED)
        self.assertEqual(EvalState.RED, eval_state_out)

        rule.set_item_state(item_name, State.create(StateType.STRING, OpeningValue.OPEN.name))
        eval_item = EvalItem(EvalType.OPEN, item_name)

        eval_state_out = rule._check_eval_item(eval_item, EvalState.GREEN)
        self.assertEqual(EvalState.RED, eval_state_out)
        eval_state_out = rule._check_eval_item(eval_item, EvalState.ORANGE)
        self.assertEqual(EvalState.RED, eval_state_out)
        eval_state_out = rule._check_eval_item(eval_item, EvalState.RED)
        self.assertEqual(EvalState.RED, eval_state_out)

    def test_check_eval_item_elec_dimmer(self):

        rule = MockLedStatusRule()
        item_name = 'elec'

        rule.set_item_state(item_name, State.create(StateType.DIMMER, 0.0))
        eval_item = EvalItem(EvalType.ELEC, item_name)

        eval_state_out = rule._check_eval_item(eval_item, EvalState.GREEN)
        self.assertEqual(EvalState.GREEN, eval_state_out)
        eval_state_out = rule._check_eval_item(eval_item, EvalState.RED)
        self.assertEqual(EvalState.RED, eval_state_out)

        rule.set_item_state(item_name, State.create(StateType.DIMMER, 1.0))
        eval_item = EvalItem(EvalType.ELEC, item_name)

        eval_state_out = rule._check_eval_item(eval_item, EvalState.GREEN)
        self.assertEqual(EvalState.RED, eval_state_out)
        eval_state_out = rule._check_eval_item(eval_item, EvalState.RED)
        self.assertEqual(EvalState.RED, eval_state_out)

    def test_check_eval_item_elec_decimal(self):

        rule = MockLedStatusRule()
        item_name = 'elec'

        rule.set_item_state(item_name, State.create(StateType.DECIMAL, 0.0))
        eval_item = EvalItem(EvalType.ELEC, item_name)

        eval_state_out = rule._check_eval_item(eval_item, EvalState.GREEN)
        self.assertEqual(EvalState.GREEN, eval_state_out)
        eval_state_out = rule._check_eval_item(eval_item, EvalState.RED)
        self.assertEqual(EvalState.RED, eval_state_out)

        rule.set_item_state(item_name, State.create(StateType.DECIMAL, 1.0))
        eval_item = EvalItem(EvalType.ELEC, item_name)

        eval_state_out = rule._check_eval_item(eval_item, EvalState.GREEN)
        self.assertEqual(EvalState.RED, eval_state_out)
        eval_state_out = rule._check_eval_item(eval_item, EvalState.RED)
        self.assertEqual(EvalState.RED, eval_state_out)

    def test_check_eval_item_elec_switch(self):

        rule = MockLedStatusRule()
        item_name = 'elec'

        rule.set_item_state(item_name, State.create(StateType.SWITCH, OnOffValue.OFF))
        eval_item = EvalItem(EvalType.ELEC, item_name)

        eval_state_out = rule._check_eval_item(eval_item, EvalState.GREEN)
        self.assertEqual(EvalState.GREEN, eval_state_out)
        eval_state_out = rule._check_eval_item(eval_item, EvalState.RED)
        self.assertEqual(EvalState.RED, eval_state_out)

        rule.set_item_state(item_name, State.create(StateType.SWITCH, OnOffValue.ON))
        eval_item = EvalItem(EvalType.ELEC, item_name)

        eval_state_out = rule._check_eval_item(eval_item, EvalState.GREEN)
        self.assertEqual(EvalState.RED, eval_state_out)
        eval_state_out = rule._check_eval_item(eval_item, EvalState.RED)
        self.assertEqual(EvalState.RED, eval_state_out)

        rule.set_item_state(item_name, State.create(StateType.ONOFF, OnOffValue.OFF))
        eval_item = EvalItem(EvalType.ELEC, item_name)

        eval_state_out = rule._check_eval_item(eval_item, EvalState.GREEN)
        self.assertEqual(EvalState.GREEN, eval_state_out)
        eval_state_out = rule._check_eval_item(eval_item, EvalState.RED)
        self.assertEqual(EvalState.RED, eval_state_out)

        rule.set_item_state(item_name, State.create(StateType.ONOFF, OnOffValue.ON))
        eval_item = EvalItem(EvalType.ELEC, item_name)

        eval_state_out = rule._check_eval_item(eval_item, EvalState.GREEN)
        self.assertEqual(EvalState.RED, eval_state_out)
        eval_state_out = rule._check_eval_item(eval_item, EvalState.RED)
        self.assertEqual(EvalState.RED, eval_state_out)

    def test_check_eval_item_invalid(self):

        rule = MockLedStatusRule()
        item_name = 'elec'

        rule.set_item_state(item_name, State.create(StateType.SWITCH, None))
        eval_item = EvalItem(EvalType.ELEC, item_name)

        eval_state_out = rule._check_eval_item(eval_item, EvalState.GREEN)
        self.assertEqual(EvalState.RED, eval_state_out)
        eval_state_out = rule._check_eval_item(eval_item, EvalState.RED)
        self.assertEqual(EvalState.RED, eval_state_out)

        rule.set_item_state(item_name, State.create(StateType.STRING, 'UNKNOWN'))
        eval_item = EvalItem(EvalType.OPEN, item_name)

        eval_state_out = rule._check_eval_item(eval_item, EvalState.GREEN)
        self.assertEqual(EvalState.RED, eval_state_out)
        eval_state_out = rule._check_eval_item(eval_item, EvalState.RED)
        self.assertEqual(EvalState.RED, eval_state_out)

        rule.set_item_state(item_name, State.create(StateType.DIMMER, 'nonumber'))
        eval_item = EvalItem(EvalType.ELEC, item_name)

        eval_state_out = rule._check_eval_item(eval_item, EvalState.GREEN)
        self.assertEqual(EvalState.RED, eval_state_out)
        eval_state_out = rule._check_eval_item(eval_item, EvalState.RED)
        self.assertEqual(EvalState.RED, eval_state_out)

        rule.set_item_state(item_name, State.create(StateType.DECIMAL, 'nonumber'))
        eval_item = EvalItem(EvalType.ELEC, item_name)

        eval_state_out = rule._check_eval_item(eval_item, EvalState.GREEN)
        self.assertEqual(EvalState.RED, eval_state_out)
        eval_state_out = rule._check_eval_item(eval_item, EvalState.RED)
        self.assertEqual(EvalState.RED, eval_state_out)

    def prepare_system(self, rule: MockLedStatusRule, led_red, child_red):
        rule.clear()

        for eval_set in rule.eval_config:

            if led_red is None:
                state = None
            elif led_red:
                state = State.create(StateType.STRING, 'RED')
            else:
                state = State.create(StateType.STRING, 'GREEN')
            rule.set_item_state(eval_set.led_item, state)

            for eval_item in eval_set.child_items:
                if eval_item.eval_type == EvalType.ELEC:
                    if child_red is None:
                        state = None
                    elif child_red:
                        state = State.create(StateType.SWITCH, OnOffValue.ON)
                    else:
                        state = State.create(StateType.SWITCH, OnOffValue.OFF)
                    rule.set_item_state(eval_item.item_name, state)
                elif eval_item.eval_type == EvalType.OPEN:
                    if child_red is None:
                        state = None
                    elif child_red:
                        state = State.create(StateType.STRING, OpeningValue.OPEN.name)
                    else:
                        state = State.create(StateType.STRING, OpeningValue.CLOSED.name)
                    rule.set_item_state(eval_item.item_name, state)
                else:
                    raise NotImplementedError()

    def test_cron_no_changes(self):

        rule = MockLedStatusRule()
        self.prepare_system(rule, False, False)

        action = Action.create_cron_action('no_matter')
        rule.notify_action(action)

        self.assertEqual(0, len(rule.sent_list))

    def test_cron_send_changes(self):

        rule = MockLedStatusRule()
        self.prepare_system(rule, True, False)

        action = Action.create_cron_action('no_matter')
        rule.notify_action(action)

        self.assertEqual(len(rule.eval_config), len(rule.sent_list))

        for i in range(0, len(rule.eval_config)):
            eval_set = rule.eval_config[i]
            sent = rule.sent_list[i]
            self.assertEqual(eval_set.led_item, sent.led_item)
            self.assertEqual(sent.check_diff_and_update, True)
            self.assertEqual(sent.eval_set, EvalState.GREEN)

    def test_cron_single_change(self):

        rule = MockLedStatusRule()
        self.prepare_system(rule, False, False)

        # EvalSet('r03', 'valLedHall11', [
        #     EvalItem(EvalType.ELEC, 'valLiBathUpCeil'),
        #     EvalItem(EvalType.ELEC, 'valLiBathUpMirror'),
        #     EvalItem(EvalType.ELEC, 'valLiSleeping')

        led_item = 'valLedHall11'
        child_item = 'valLiBathUpMirror'
        # ELEC; overwrite
        rule.set_item_state(child_item, State.create(StateType.SWITCH, OnOffValue.ON))

        action = Action()
        action.channel = Channel.create_item(child_item)
        rule.notify_action(action)

        self.assertEqual(1, len(rule.sent_list))

        sent = rule.sent_list[0]
        self.assertEqual(led_item, sent.led_item)
        self.assertEqual(sent.check_diff_and_update, False)
        self.assertEqual(sent.eval_set, EvalState.RED)
