from abc import abstractmethod
import csv

from cadCAD.configuration.utils import config_sim
from cadCAD.configuration import Experiment
from cadCAD.engine import ExecutionContext, Executor


class BaseModel():

    def __init__(self):
        self.btc_blockreward_data = []
        self.btc_diff_data = []
        self.btc_price_data = []

    def initialize_state(self):
        # Populate historical data
        self.populate_from_csv(self.btc_blockreward_data, 'data/btc_per_block.csv')
        self.populate_from_csv(self.btc_diff_data, 'data/btc_diff.csv')
        self.populate_from_csv(self.btc_price_data, 'data/btc_price.csv')
        # Constants
        self.koomey_period_in_hours = 11520
        self.diff_smoothing_factor = 5760
        self.price_smoothing_factor = 12960
        self.scaling_factor = (self.btc_price_data[0] *self.btc_blockreward_data[0]) / (self.btc_diff_data[0] // 2)
        self.partial_state_update_blocks = [
            {
                'policies': {
                    'btc_diff': lambda p, ss, sh, ps: self.p_btc_diff(p, ss, sh, ps),
                    'btc_price': lambda p, ss, sh, ps: self.p_btc_price(p, ss, sh, ps),
                    'btc_blockreward': lambda p, ss, sh, ps: self.p_btc_blockreward(p, ss, sh, ps),
                },
                'variables': {
                    'btc_diff': lambda p, ss, sh, ps, i: self.s_btc_diff(p, ss, sh, ps, i),
                    'btc_price': lambda p, ss, sh, ps, i: self.s_btc_price(p, ss, sh, ps, i),
                    'btc_blockreward': lambda p, ss, sh, ps, i: self.s_btc_blockreward(p, ss, sh, ps, i)
                }
            },
            {
                'policies': {
                    'kdiff': lambda p, ss, sh, ps: self.p_kdiff(p, ss, sh, ps)
                },
                'variables': {
                    'kdiff': lambda p, ss, sh, ps, i: self.s_kdiff(p, ss, sh, ps, i)
                }
            },
            {
                'policies': {
                    'kdiff_smoothed': lambda p, ss, sh, ps: self.p_kdiff_smoothed(p, ss, sh, ps),
                    'blockreward_smoothed': lambda p, ss, sh, ps: self.p_blockreward_smoothed(p, ss, sh, ps)
                },
                'variables': {
                    'kdiff_smoothed': lambda p, ss, sh, ps, i: self.s_kdiff_smoothed(p, ss, sh, ps, i),
                    'blockreward_smoothed': lambda p, ss, sh, ps, i: self.s_blockreward_smoothed(p, ss, sh, ps, i)
                }
            },
            {
                'policies': {
                    'led_price': lambda p, ss, sh, ps: self.p_led_price(p, ss, sh, ps)
                },
                'variables': {
                    'led_price': lambda p, ss, sh, ps, i: self.s_led_price(p, ss, sh, ps, i)
                }
            }
        ]

    @abstractmethod
    def apply_smoothing(self, old_value, new_value, smoothing_factor):
        pass
    
    @abstractmethod
    def get_initial_state(self):
        pass

    def populate_from_csv(self, vec, filename):
        with open(filename, newline='', mode='r') as csv_file:
            csv_reader = csv.reader(csv_file)
            line_count = 0
            for row in csv_reader:
                if line_count == 0:
                    line_count += 1
                    continue
                vec.append(float(row[0]))
                line_count += 1

    # Assume timestep of 1 hour
    def p_btc_blockreward(self, params, substep, state_history, previous_state):
        new_btc_blockreward = self.btc_blockreward_data[previous_state['timestep']]
        return ({'new_btc_blockreward': new_btc_blockreward})

    def s_btc_blockreward(self, params, substep, state_history, previous_state, policy_input):
        return ('btc_blockreward', policy_input['new_btc_blockreward'])

    def p_btc_diff(self, params, substep, state_history, previous_state):
        new_btc_diff = self.btc_diff_data[previous_state['timestep']]
        return ({'new_btc_diff': new_btc_diff})

    def s_btc_diff(self, params, substep, state_history, previous_state, policy_input):
        return ('btc_diff', policy_input['new_btc_diff'])

    def p_btc_price(self, params, substep, state_history, previous_state):
        new_btc_price = self.btc_price_data[previous_state['timestep']]
        return ({'new_btc_price': new_btc_price})

    def s_btc_price(self, params, substep, state_history, previous_state, policy_input):
        return ('btc_price', policy_input['new_btc_price'])

    def p_kdiff(self, params, substep, state_history, previous_state):
        exponent = 1 + (previous_state['timestep'] / self.koomey_period_in_hours)
        denominator = 2 ** exponent
        return ({'new_kdiff': previous_state['btc_diff'] / denominator})

    def s_kdiff(self, params, substep, state_history, previous_state, policy_input):
        return ('kdiff', policy_input['new_kdiff'])

    def p_kdiff_smoothed(self, params, substep, state_history, previous_state):
        new_kdiff_smoothed = self.apply_smoothing(previous_state['kdiff_smoothed'], previous_state['kdiff'], self.diff_smoothing_factor)
        return ({'new_kdiff_smoothed': new_kdiff_smoothed})

    def s_kdiff_smoothed(self, params, substep, state_history, previous_state, policy_input):
        return ('kdiff_smoothed', policy_input['new_kdiff_smoothed'])

    def p_blockreward_smoothed(self, params, substep, state_history, previous_state):
        cur_blockreward = previous_state['btc_blockreward'] * previous_state['btc_price']
        new_blockreward_smoothed = self.apply_smoothing(previous_state['blockreward_smoothed'], cur_blockreward, self.price_smoothing_factor)
        return ({'new_blockreward_smoothed': new_blockreward_smoothed})

    def s_blockreward_smoothed(self, params, substep, state_history, previous_state, policy_input):
        return ('blockreward_smoothed', policy_input['new_blockreward_smoothed'])

    def p_led_price(self, params, substep, state_history, previous_state):
        new_led_price = previous_state['blockreward_smoothed'] / previous_state['kdiff_smoothed']
        return ({'new_led_price': new_led_price / self.scaling_factor})

    def s_led_price(self, params, substep, state_history, previous_state, policy_input):
        return ('led_price', policy_input['new_led_price'])

