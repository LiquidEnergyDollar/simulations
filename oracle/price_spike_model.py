import numpy as np
import math
from base_model import BaseModel
from smoothing_function import SmoothingFunction

class PriceSpikeModel(BaseModel):

    def __init__(
            self, 
            price_smoothing_function: SmoothingFunction, 
            diff_smoothing_function: SmoothingFunction,
            btc_price
        ):
        super().__init__(price_smoothing_function, diff_smoothing_function)
        self.btc_price = btc_price

    def get_initial_state(self, params):
        diff_convergence = params['diff_convergence']
        return {
            'btc_diff': 1,
            'btc_price': self.btc_price,
            'btc_blockreward': 1,
            'kdiff': 1,
            'kdiff_smoothed': 1,
            'blockreward_smoothed': self.btc_price,
            'led_price': self.btc_price / ((self.btc_price - 1) * params['diff_convergence'][0])
        }
    
    
    def initialize_state(self):
        BaseModel.initialize_state(self)
        self.scaling_factor = 2
    # Assume block rewards are constant
    def p_btc_blockreward(self, params, substep, state_history, previous_state):
        new_btc_blockreward = previous_state['btc_blockreward']
        return ({'new_btc_blockreward': new_btc_blockreward})

    # Diff converges on price
    def p_btc_diff(self, params, substep, state_history, previous_state):
        old_btc_diff = previous_state['btc_diff']
        diff_delta = (previous_state['btc_price'] - old_btc_diff) * params['diff_convergence']
        new_btc_diff = old_btc_diff + diff_delta
        return ({'new_btc_diff': new_btc_diff})

    # Assume BTC price is constant
    def p_btc_price(self, params, substep, state_history, previous_state):
        old_btc_price = previous_state['btc_price']
        return ({'new_btc_price': old_btc_price})
    
    # Kdiff is ignored for this simulation
    def p_kdiff(self, params, substep, state_history, previous_state):
        return ({'new_kdiff': previous_state['btc_diff']})

    # No scaling
    def p_led_price(self, params, substep, state_history, previous_state):
        new_led_price = previous_state['blockreward_smoothed'] / previous_state['kdiff_smoothed']
        return ({'new_led_price': new_led_price})