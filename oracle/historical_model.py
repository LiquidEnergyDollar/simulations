import csv

from cadCAD.configuration.utils import config_sim
from cadCAD.configuration import Experiment
from cadCAD.engine import ExecutionContext, Executor

def apply_ema(old_value, new_value, smoothing_factor):
    delta = new_value - old_value
    change = delta / smoothing_factor
    return old_value + change

def populate_from_csv(vec, filename):
    with open(filename, newline='', mode='r') as csv_file:
        csv_reader = csv.reader(csv_file)
        line_count = 0
        for row in csv_reader:
            if line_count == 0:
                line_count += 1
                continue
            vec.append(float(row[0]))
            line_count += 1

# Populate historical data
btc_blockreward_data = []
populate_from_csv(btc_blockreward_data, 'data/btc_per_block.csv')

btc_diff_data = []
populate_from_csv(btc_diff_data, 'data/btc_diff.csv')

btc_price_data = []
populate_from_csv(btc_price_data, 'data/btc_price.csv')

# Constants
koomey_period_in_hours = 11520
diff_smoothing_factor = 5760
price_smoothing_factor = 12960
scaling_factor = (btc_price_data[0] * btc_blockreward_data[0]) / (btc_diff_data[0] // 2)

# Assume timestep of 1 hour
def p_btc_blockreward(params, substep, state_history, previous_state):
    new_btc_blockreward = btc_blockreward_data[previous_state['timestep']]
    return ({'new_btc_blockreward': new_btc_blockreward})

def s_btc_blockreward(params, substep, state_history, previous_state, policy_input):
    return ('btc_blockreward', policy_input['new_btc_blockreward'])

def p_btc_diff(params, substep, state_history, previous_state):
    new_btc_diff = btc_diff_data[previous_state['timestep']]
    return ({'new_btc_diff': new_btc_diff})

def s_btc_diff(params, substep, state_history, previous_state, policy_input):
    return ('btc_diff', policy_input['new_btc_diff'])

def p_btc_price(params, substep, state_history, previous_state):
    new_btc_price = btc_price_data[previous_state['timestep']]
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
    'btc_diff': btc_diff_data[0],
    'btc_price': btc_price_data[0],
    'btc_blockreward': btc_blockreward_data[0],
    'kdiff': btc_diff_data[0] // 2,
    'kdiff_smoothed': btc_diff_data[0] // 2,
    'blockreward_smoothed': btc_price_data[0] * btc_blockreward_data[0],
    'led_price': 1
}
