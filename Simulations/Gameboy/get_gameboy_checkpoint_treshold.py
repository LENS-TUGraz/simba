# -*- coding: utf-8 -*-
"""
Obtain the minimum checkpoint voltage threshold for different capacitances
such that the checkpoint can still be completed, even if no energy can be harvested (i.e., I_IN = 0)
"""

import pandas as pd
import numpy as np

# Configuration(s) for simulation

from Gameboy import load_config, converter_config
from Simba import run_tradeoff_exploration

# There's no incoming harvesting current
harvest_config_none = {
    'type' :  'Artificial',
    'settings' : {'shape' : 'const',
                  'i_high' : 0,
                  'v_oc' : 3}
    }

vhigh=4.87
capacitor_config_tmp = {'type' : 'IdealCapacitor',
                        'settings': {'capacitance' : 2000e-6,
                                     'v_initial' : vhigh,
                                     'v_rated' : 10}
    }

converter_config['settings']['v_out_ok_enable'] = vhigh

# For later experiments, we need to know the optimal v_chkpt of all tested capacitances
# caps = list(np.arange(300e-6, 6800e-6, 100e-6)) + [6800e-6] #, 220e-6, 260e-6, 360e-6, 560e-6]
# caps = [round(c,5) for c in caps]

# Check for the Gameboy's default value for now
caps = [3300e-6]

#%%
# Default configuration of Gameboy
base_config = {'harvester' : harvest_config_none,
                'load' : load_config,
                'capacitor' : capacitor_config_tmp,
                'converter' : converter_config,
                'sim_time' : 10}

settings = {'normalize_stats' : False}
# We check for different v_checkpoint settings, if the checkpoint has been successful
# Parameters to explore: 
params = {'load.v_checkpoint' : list(np.arange(3.3, vhigh, 0.01))}
# Metrics to obtain
metrics = [{'module' : 'load', 'params' : ['num_CHECKPOINT_successful']}]

thresholds = {}

if __name__ == '__main__':
    # Obtain the optimal checkpoint for each capacitance
    for cap in caps:
        base_config['capacitor']['settings']['capacitance'] = cap
        base_config['capacitor']['settings']['v_initial'] = vhigh
        
        result = run_tradeoff_exploration(params, metrics, base_config,settings)

        # The minimum V_Checkpoint, at which a checkpoint was successful is the optimal threshold
        result = pd.DataFrame(result).sort_values('load.v_checkpoint')
        v_threshold_min = result[result['load.num_CHECKPOINT_successful'] >= 1]
        
        if len(v_threshold_min) == 0:
            print(f"Could not find minimum threshold for C = {cap}!")
            v_threshold_min = None
        else:
            v_threshold_min = round(v_threshold_min.iloc[0]['load.v_checkpoint'], 2)
            print(f"Minimum Checkpoint-Threshold-Voltage @ C={int(cap*1e6)} :{v_threshold_min}")
            
        thresholds[cap] = v_threshold_min