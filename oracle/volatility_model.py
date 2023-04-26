import numpy as np
import math

def apply_ema(old_value, new_value, smoothing_factor):
    delta = new_value - old_value
    change = delta / smoothing_factor
    return old_value + change

# Constants
hours_in_year = 8760
# Volatility changes as sqrt of time
vol_yearly_to_hour = math.sqrt(8760)
koomey_period_in_hours = 11520
diff_smoothing_factor = 5760
price_smoothing_factor = 12960
scaling_factor = 2

def get_vol_movement(old_value, yearly_std_dev, trend):
    hourly_std_dev = yearly_std_dev / vol_yearly_to_hour
    vol_delta = np.random.normal(1, hourly_std_dev, 1)[0]
    trend_delta = 1 + (trend / hours_in_year)
    return old_value * vol_delta * trend_delta

# Volatility parameters
params = {
    # Standard deviation for yearly volatility
    'diff_vol_std_dev': [0],
    'price_vol_std_dev': [0],

    # Trend values in yearly APY
    'diff_trend': [0],
    'price_trend': [0]
}

# Assume timestep of 1 hour

# Assume block rewards are constant
def p_btc_blockreward(params, substep, state_history, previous_state):
    new_btc_blockreward = previous_state['btc_blockreward']
    return ({'new_btc_blockreward': new_btc_blockreward})

def s_btc_blockreward(params, substep, state_history, previous_state, policy_input):
    return ('btc_blockreward', policy_input['new_btc_blockreward'])

def p_btc_diff(params, substep, state_history, previous_state):
    old_btc_diff = previous_state['btc_diff']
    new_btc_diff = get_vol_movement(old_btc_diff, params['diff_vol_std_dev'], params['diff_trend'])
    return ({'new_btc_diff': new_btc_diff})

def s_btc_diff(params, substep, state_history, previous_state, policy_input):
    return ('btc_diff', policy_input['new_btc_diff'])

def p_btc_price(params, substep, state_history, previous_state):
    old_btc_price = previous_state['btc_price']
    new_btc_price = get_vol_movement(old_btc_price, params['price_vol_std_dev'], params['price_trend'])
    return ({'new_btc_price': new_btc_price})

def s_btc_price(params, substep, state_history, previous_state, policy_input):
    return ('btc_price', policy_input['new_btc_price'])

def p_kdiff(params, substep, state_history, previous_state):
    exponent = 1 + (previous_state['timestep'] / koomey_period_in_hours)
    denominator = 2 ** exponent
    return ({'new_kdiff': previous_state['btc_diff'] / denominator})

def s_kdiff(params, substep, state_history, previous_state, policy_input):
    return ('kdiff', policy_input['new_kdiff'])

def p_kdiff_smoothed(params, substep, state_history, previous_state):
    new_kdiff_smoothed = apply_ema(previous_state['kdiff_smoothed'], previous_state['kdiff'], diff_smoothing_factor)
    return ({'new_kdiff_smoothed': new_kdiff_smoothed})

def s_kdiff_smoothed(params, substep, state_history, previous_state, policy_input):
    return ('kdiff_smoothed', policy_input['new_kdiff_smoothed'])

def p_blockreward_smoothed(params, substep, state_history, previous_state):
    cur_blockreward = previous_state['btc_blockreward'] * previous_state['btc_price']
    new_blockreward_smoothed = apply_ema(previous_state['blockreward_smoothed'], cur_blockreward, price_smoothing_factor)
    return ({'new_blockreward_smoothed': new_blockreward_smoothed})

def s_blockreward_smoothed(params, substep, state_history, previous_state, policy_input):
    return ('blockreward_smoothed', policy_input['new_blockreward_smoothed'])

def p_led_price(params, substep, state_history, previous_state):
    new_led_price = previous_state['blockreward_smoothed'] / previous_state['kdiff_smoothed']
    return ({'new_led_price': new_led_price / scaling_factor})

def s_led_price(params, substep, state_history, previous_state, policy_input):
    return ('led_price', policy_input['new_led_price'])

partial_state_update_blocks = [
    {
        'policies': {
            'btc_diff': p_btc_diff,
            'btc_price': p_btc_price,
            'btc_blockreward': p_btc_blockreward
        },
        'variables': {
            'btc_diff': s_btc_diff,
            'btc_price': s_btc_price,
            'btc_blockreward': s_btc_blockreward
        }
    },
    {
        'policies': {
            'kdiff': p_kdiff
        },
        'variables': {
            'kdiff': s_kdiff
        }
    },
    {
        'policies': {
            'kdiff_smoothed': p_kdiff_smoothed,
            'blockreward_smoothed': p_blockreward_smoothed
        },
        'variables': {
            'kdiff_smoothed': s_kdiff_smoothed,
            'blockreward_smoothed': s_blockreward_smoothed
        }
    },
    {
        'policies': {
            'led_price': p_led_price
        },
        'variables': {
            'led_price': s_led_price
        }
    }
]

initial_state = {
    'btc_diff': 1,
    'btc_price': 1,
    'btc_blockreward': 1,
    'kdiff': 0.5,
    'kdiff_smoothed': 0.5,
    'blockreward_smoothed': 1,
    'led_price': 1
}
