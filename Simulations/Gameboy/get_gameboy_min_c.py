# -*- coding: utf-8 -*-
"""
Obtain minimum capacitance for a given voltage threshold, where a 
full RESTORE+CHECKPOINT cycle is possible if no harvested energy is incoming
"""


import pandas as pd
import numpy as np

# Configuration(s) for simulation

from Gameboy import harvest_config_solar, load_config, converter_config
from Simba import run_tradeoff_exploration

# No incoming harvesting energy
harvest_config_none = {
    'type' :  'Artificial',
    'settings' : {'shape' : 'const',
                  'i_high' : 0,
                  'v_oc' : 3}
    }

capacitor_config_tmp = {'type' : 'IdealCapacitor',
                        'settings': {'capacitance' : 3300e-6,
                                     'v_initial' : 4.87,
                                     'v_rated' : 10}
    }

# The minimum capacitance will be somewhere between 200 und  600 uF
caps = list(np.arange(200e-6, 600e-6, 20e-6))
caps = [round(c,5) for c in caps]

#%%
base_config = {'harvester' : harvest_config_solar,
                'load' : load_config,
                'capacitor' : capacitor_config_tmp,
                'converter' : converter_config,
                'sim_time' : 10}

metrics = [{'module' : 'load', 'params' : ['num_CHECKPOINT_successful']}]

thresholds = {}

min_caps = { #known from previous experiments; just skip anything below that
    3.63 : 500e-6,
    3.97 : 500e-6,
    4.3  : 300e-6,
    4.61 : 200e-6,
    4.87 : 200e-6}

if __name__ == '__main__':
    # For all V high threshold options, get the mininum feasible capacitance
    for vhigh in [3.63, 3.97, 4.3, 4.61, 4.87]:
        for cap in caps:
            
            if cap < min_caps[vhigh]:
                continue
            
            base_config['capacitor']['settings']['capacitance'] = cap
            base_config['capacitor']['settings']['v_initial'] = vhigh
            
            params = {'load.v_checkpoint' : list(np.arange(3.4, vhigh, 0.01))}
            
            result = run_tradeoff_exploration(params, metrics, base_config)
            result = pd.DataFrame(result).sort_values('load.v_checkpoint')
            v_threshold_min = result[result['load.num_CHECKPOINT_successful'] >= 1]
            
            #This is the first time, we were able to save a checkpoint -> store minimum C and exit loop
            if len(v_threshold_min) != 0:
                v_threshold_min = round(v_threshold_min.iloc[0]['load.v_checkpoint'], 2)
                thresholds[vhigh] = cap
                print(f"Min C for {vhigh}:{cap}")
                break
                
                