import numpy as np
import math
from base_model import BaseModel

class VolatilityModel(BaseModel):
    #EMA Smoothing
    def apply_smoothing(self, old_value, new_value, smoothing_factor):
        delta = new_value - old_value
        change = delta / smoothing_factor
        return old_value + change


    def get_initial_state(self):
        return {
            'btc_diff': 1,
            'btc_price': 1,
            'btc_blockreward': 1,
            'kdiff': 0.5,
            'kdiff_smoothed': 0.5,
            'blockreward_smoothed': 1,
            'led_price': 1
        }
    
    
    def initialize_state(self):
        BaseModel.initialize_state(self)
        self.scaling_factor = 2
        self.hours_in_year = 8760
        # Volatility changes as sqrt of time
        self.vol_yearly_to_hour = math.sqrt(self.hours_in_year)
        # Volatility parameters
        self.params = {
            # Standard deviation for yearly volatility
            'diff_vol_std_dev': [0],
            'price_vol_std_dev': [0],

            # Trend values in yearly APY
            'diff_trend': [0],
            'price_trend': [0]
        }

    def get_vol_movement(self, old_value, yearly_std_dev, trend):
        hourly_std_dev = yearly_std_dev / self.vol_yearly_to_hour
        vol_delta = np.random.normal(1, hourly_std_dev, 1)[0]
        trend_delta = 1 + (trend / self.hours_in_year)
        return old_value * vol_delta * trend_delta

    # Assume block rewards are constant
    def p_btc_blockreward(self, params, substep, state_history, previous_state):
        new_btc_blockreward = previous_state['btc_blockreward']
        return ({'new_btc_blockreward': new_btc_blockreward})

    def p_btc_diff(self, params, substep, state_history, previous_state):
        old_btc_diff = previous_state['btc_diff']
        new_btc_diff = self.get_vol_movement(old_btc_diff, params['diff_vol_std_dev'], params['diff_trend'])
        return ({'new_btc_diff': new_btc_diff})

    def p_btc_price(self, params, substep, state_history, previous_state):
        old_btc_price = previous_state['btc_price']
        new_btc_price = self.get_vol_movement(old_btc_price, params['price_vol_std_dev'], params['price_trend'])
        return ({'new_btc_price': new_btc_price})

    def p_kdiff_smoothed(self, params, substep, state_history, previous_state):
        new_kdiff_smoothed = self.apply_smoothing(previous_state['kdiff_smoothed'], previous_state['kdiff'], self.diff_smoothing_factor)
        return ({'new_kdiff_smoothed': new_kdiff_smoothed})

    def p_blockreward_smoothed(self, params, substep, state_history, previous_state):
        cur_blockreward = previous_state['btc_blockreward'] * previous_state['btc_price']
        new_blockreward_smoothed = self.apply_smoothing(previous_state['blockreward_smoothed'], cur_blockreward, self.price_smoothing_factor)
        return ({'new_blockreward_smoothed': new_blockreward_smoothed})