# -*- coding: utf-8 -*-
"""
Compare how the checkpoint voltage thresholds affects forward progress
of the Gameboy at different illuminance levels
"""

from Gameboy import capacitor_config, converter_config, load_config, harvest_config_solar
from Simba import run_tradeoff_exploration
import pandas as pd

#%%
base_config = {'harvester' : harvest_config_solar,
                'load' : load_config,
                'capacitor' : capacitor_config,
                'converter' : converter_config,
                'sim_time' : 300}

# Explore the forward progress for different checkpoint/lux combinations
params = {'load.v_checkpoint': [3.4, 3.35, 3.34], 'harvester.lux' : [10000, 13000, 15000, 18000, 20000]}
metrics = [{'module' : 'load', 'params' : ['time_total', 'time_COMPUTE_useful', 'energy_COMPUTE_useful', 'time_COMPUTE', 'energy_COMPUTE', 'energy_total','num_CHECKPOINT_successful', 'num_RESTORE_successful', 'num_CHECKPOINT_failed', 'forward_progress']}]

settings = {'normalize_stats' : True} #Normalize stats to get 'fair' forward progress results

if __name__ == '__main__':
    result = run_tradeoff_exploration(params, metrics, base_config, settings)
   
    result = pd.DataFrame(result)
    r_334 = result[result['load.v_checkpoint'] == 3.34].set_index('harvester.lux')
    r_335 = result[result['load.v_checkpoint'] == 3.35].set_index('harvester.lux')
    r_340 = result[result['load.v_checkpoint'] == 3.40].set_index('harvester.lux')
    
    print("Improvement of optimal (safe) v_checkpoint:")
    print(r_335['load.forward_progress'] /  r_340['load.forward_progress'])
    print("Improvement of optimal (greedy) v_checkpoint:")
    print(r_334['load.forward_progress'] /  r_340['load.forward_progress'])
