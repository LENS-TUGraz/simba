# -*- coding: utf-8 -*-
"""
Simulate Gameboy for using a irradiance traces from an entire month (e.g., either June or January 2023).
The trade-off exploration tool is used to simulate each day from 5:00 - 20:00 independently and concurrently 
(i.e., we can assume that after each night, the device is shut-off anyway.)
During simulation, the entire simulation trace of each day is stored (in Results_xxx23/Raw) and can be processed using 'process_gameboy_longterm_data.py'
"""

import pandas as pd

# Configuration(s) for simulation
from Gameboy import harvest_config_solar_long, capacitor_config, converter_config, load_config
from Simba import run_tradeoff_exploration

def hours_to_seconds(hours):
    return hours * 60 * 60

def days_to_seconds(days):
    return days * 24 * 60 * 60

#%%

# Choose data set
file = 'NREL/2023jun.json'
#file = 'NREL/2023jan.json'

base_config = { 'harvester' : harvest_config_solar_long,
                'load' : load_config,
                'capacitor' : capacitor_config,
                'converter' : converter_config,
                'sim_time' : hours_to_seconds(15)} #we always simulate for 15h (from 5 - 20h)

settings = {'timestep' : 5e-3,
            'normalize_stats' : False,
            'store_log_data' : True} #Store the raw file, we extract the logging later

harvest_config_solar_long['settings']['file'] = file
converter_config['settings']['vout_ok_high'] = 3.63   #3.97
capacitor_config['settings']['capacitance'] = 5100e-6 #3300e-6
load_config['settings']['v_checkpoint'] = 3.34        #optimal v_checkpoint for 5100e-6


metrics = [{'module' : 'load', 'params' : ['time_total', 'time_COMPUTE_useful', 'energy_COMPUTE_useful', 'energy_total','num_CHECKPOINT_successful', 'num_RESTORE_successful', 'num_CHECKPOINT_failed', 'num_COMPUTE_useful', 'forward_progress', 'time_off_mean', 'time_off_max', 'time_compute_mean', 'time_unavailable_mean', 'time_unavailable_max', 'time_unavailable_95', 'time_available_min', 'time_available_mean', 'time_available_95', 'time_available_max']},
           {'module' : 'harvester', 'params' : ['energy_total', 'energy_max', 'i_in_max', 'i_in_mean', 'p_in_max', 'p_in_mean', 'irr_min', 'irr_mean']}]


# We perform seperate simulations for each day (in parallel), since at night we won't operate anyway
start_times = [hours_to_seconds(5) + days_to_seconds(day) for day in range(0,30)]

if __name__ == '__main__':

    params = {'harvester.t_start' : start_times}
#    result_folder = f'./Results_{datetime.datetime.now().strftime("%Y%m%d%H%M%S")}'
    result_folder = f'./Results_{"Jun23" if "jun" in file else "Jan23"}/Raw'

    settings['log_path'] = result_folder #we store the full traces for each day there
    result = run_tradeoff_exploration(params, metrics, base_config, settings)
    result = pd.DataFrame(result)
    result.to_pickle(f"{result_folder}/ResultSolarGameboyDay.pkl")
