# -*- coding: utf-8 -*-
"""
Process long-term simulation data of Gameboy.
Retrieve traces from each day from 'Results_xxx23/Raw' and extract hourly 
metrics such as forward progress and unavailility.
Store overall statistics and harvesting traces in 'Results_xxx23' such that it
can be plotted later using 'plot_gameboy_long_term_data.py'
"""

from Simba import load_log_from_file_pkl
import pandas as pd
import os
import matplotlib.pyplot as plt


def compute_stats(log, stepsize):     
    load_log = log.copy().reset_index(drop=True)
    stats = {}
 
    stats['num_CHECKPOINT_successful'] = len(load_log[load_log.event == 'CHECKPOINT_SUCCESS'])
    stats['num_CHECKPOINT_failed'] = len(load_log[load_log.event == 'CHECKPOINT_FAIL'])
    stats['num_RESTORE_successful'] = len(load_log[load_log.event == 'RESTORE_SUCCESS'])
    stats['num_RESTORE_failed'] = len(load_log[load_log.event == 'RESTORE_FAIL'])
    
    states_compute_useful = load_log[((load_log.state == 'COMPUTE') & load_log.valid_checkpoint) | ((load_log.state == 'COMPUTE') & (load_log.index >= load_log.index.max() - 1))]
    
    stats['num_COMPUTE_useful'] = len(states_compute_useful)
    
    for state in ['OFF', 'RESTORE', 'COMPUTE', 'CHECKPOINT']:
        stats[f'time_{state}'] = load_log[load_log.state == state].dt.sum()
    stats['time_COMPUTE_useful'] = states_compute_useful.dt.sum()
    stats['forward_progress'] = stats['time_COMPUTE_useful'] / (stats['time_COMPUTE'] + stats['time_CHECKPOINT'] + stats['time_RESTORE'] + stats['time_OFF'])
        
    stats['time_off_mean'] = load_log[load_log.state == 'OFF'].dt.mean()
    stats['time_off_max'] = load_log[load_log.state == 'OFF'].dt.max()
    
    #Get stats from the time between two computing tasks --> time we are unresponsive and user cannot do anything (off + restore)
    #compute_states = load_log[(load_log.state == 'COMPUTE') & load_log.valid_checkpoint]
    if (len(load_log[load_log.state == 'COMPUTE']) != 0) and (len(load_log[load_log.state == 'OFF']) + len(load_log[load_log.state == 'RESTORE']) != 0):
        stats['time_unavailable_95'] = (load_log[load_log.state == 'OFF'].dt.reset_index() + load_log[load_log.state == 'RESTORE'].dt.reset_index()).dt.quantile(0.95)
        stats['time_unavailable_mean'] = (load_log[load_log.state == 'OFF'].dt.reset_index() + load_log[load_log.state == 'RESTORE'].dt.reset_index()).dt.mean()
        stats['time_unavailable_max'] =  (load_log[load_log.state == 'OFF'].dt.reset_index() + load_log[load_log.state == 'RESTORE'].dt.reset_index()).dt.max()
    elif len(load_log[load_log.state == 'COMPUTE']) == 0:
        stats['time_unavailable_95'] = stepsize
        stats['time_unavailable_mean'] = stepsize
        stats['time_unavailable_max'] = stepsize
    else:             
        stats['time_unavailable_95'] = 0
        stats['time_unavailable_mean'] = 0
        stats['time_unavailable_max'] = 0
    return stats

stepsize = 1 * 60 * 60 # 1hour

PLOT = False
folders = ['Results_Jun23', 'Results_Jan23']

for folder in folders:
    total_stats = pd.DataFrame()
    for file in filter(lambda x: x.startswith('log_sim'), os.listdir(folder + '/Raw')):
        try:
            settings, cap_log, load_log, harvester_log, converter_log = load_log_from_file_pkl(os.path.join(folder + '/Raw', file))
            
            start_hour = settings['harvester.t_start'] / 3600
            day = int(file.split('log_sim')[1].split('.')[0]) #this is ugly, rewrite 
            
            harvester_log.to_pickle(f"{folder + '/harvester_log'}/harvester_log_day{day}.pkl")
            
            
            total_time = load_log.time.max() + load_log.dt.iloc[-1]
            num_steps = int(total_time / stepsize)
            
            start_time = 0
            
            #add dummy steps to ensure correct computation in each window:       
            for step in [x * stepsize for x in range(1, num_steps)]:
                if step in load_log.time.values: #step already there
                    continue
                else:
                    step_row = load_log[load_log.time < step].iloc[-1].copy()
                    step_row['dt'] = step - step_row.time
                    step_row['time'] = step
                    step_row['event'] = 'NONE'
                    load_log.loc[-1] = step_row.values
                    load_log = load_log.sort_values('time').reset_index(drop = True)
                    

            for i in range(0, num_steps):
                step_data = load_log[(load_log.time >= i * stepsize) & (load_log.time <= (i+1)*stepsize)]
                
                stats = compute_stats(step_data, stepsize)
                stats['hour'] = start_hour + i*stepsize / 3600
                stats['start_second'] = i*stepsize
                stats['day'] = day
                    
                total_stats = pd.concat([total_stats, pd.DataFrame(stats, index=[0])],  ignore_index=True)
                
                
            if PLOT:
                fig, axs = plt.subplots(nrows=4, sharex=True)
                
                load_log.plot(x='time', y=['v_cap', 'v_out'], ax=axs[0], drawstyle='steps-post')
                #converter_log.plot(x='time', y='v_stor', ax=axs[1], drawstyle='steps-post')
                #harvester_log.plot(x='time', y=['i_in', 'p_in', 'v_in'], ax=axs[1], drawstyle='steps-post')   
                
                total_stats[total_stats.day == day].plot(x='start_second', y='time_unavailable_max', ax=axs[2], drawstyle='steps-post')
                total_stats[total_stats.day == day].plot(x='start_second', y='forward_progress', ax=axs[3], drawstyle='steps-post')
                
        except Exception as e:
            print(e)
         
    total_stats.to_json(f'{folder}/{folder}.json')


