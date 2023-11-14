# -*- coding: utf-8 -*-
"""
Obtain unavailability and forward progress for 
the Gameboy at I_IN = 3.4 mA (bright sunlight)
using any parameter pair of 
V-High = {3.63, 3.97, 4.3, 4.61, 4.87} and
Cap = {0.001 - 0.0068} in 0.0001 steps
"""

from Gameboy import  harvest_config_const, capacitor_config, converter_config, load_config
from Simba import run_tradeoff_exploration
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
#%%
base_config = {'harvester' : harvest_config_const, 
                'load' : load_config,
                'capacitor' : capacitor_config,
                'converter' : converter_config,
                'sim_time' : 60}

settings = {'normalize_stats' : True}

caps = list(np.arange(300e-6, 6800e-6, 100e-6)) + [6800e-6]
caps = [round(c,5) for c in caps]

params = {'harvester.i_high': [3.4e-3], 
          'cap.capacitance': caps, 
          'converter.v_out_enable_treshold_high' : [3.63, 3.97, 4.3, 4.61, 4.87]}
map_params = {'module_to_change' : 'load',
              'param_to_change' : 'v_checkpoint',
              'module_to_map' : 'cap', #For each capacitance, let's use the optimal checkpoint voltage
              'param_to_map': 'capacitance',
               'mapping' : {0.0001: 3.63,
                            0.0002: 3.63,
                            0.00022:3.55,
                            0.00026:3.52,
                            0.00036:3.47,
                            0.00056:3.41,
                            0.0003: 3.49,
                            0.0004: 3.45,
                            0.0005: 3.42,
                            0.0006: 3.41,
                            0.0007: 3.39,
                            0.0008: 3.39,
                            0.0009: 3.38,
                            0.001: 3.37,
                            0.0011: 3.37,
                            0.0012: 3.37,
                            0.0013: 3.36,
                            0.0014: 3.36,
                            0.0015: 3.36,
                            0.0016: 3.36,
                            0.0017: 3.35,
                            0.0018: 3.35,
                            0.0019: 3.35,
                            0.002: 3.35,
                            0.0021: 3.35,
                            0.0022: 3.35,
                            0.0023: 3.35,
                            0.0024: 3.35,
                            0.0025: 3.34,
                            0.0026: 3.34,
                            0.0027: 3.34,
                            0.0028: 3.34,
                            0.0029: 3.34,
                            0.003: 3.34,
                            0.0031: 3.34,
                            0.0032: 3.34,
                            0.0033: 3.34,
                            0.0034: 3.34,
                            0.0035: 3.34,
                            0.0036: 3.34,
                            0.0037: 3.34,
                            0.0038: 3.34,
                            0.0039: 3.34,
                            0.004: 3.34,
                            0.0041: 3.34,
                            0.0042: 3.34,
                            0.0043: 3.34,
                            0.0044: 3.34,
                            0.0045: 3.34,
                            0.0046: 3.34,
                            0.0047: 3.34,
                            0.0048: 3.34,
                            0.0049: 3.33,
                            0.005: 3.33,
                            0.0051: 3.33,
                            0.0052: 3.33,
                            0.0053: 3.33,
                            0.0054: 3.33,
                            0.0055: 3.33,
                            0.0056: 3.33,
                            0.0057: 3.33,
                            0.0058: 3.33,
                            0.0059: 3.33,
                            0.006: 3.33,
                            0.0061: 3.33,
                            0.0062: 3.33,
                            0.0063: 3.33,
                            0.0064: 3.33,
                            0.0065: 3.33,
                            0.0066: 3.33,
                            0.0067: 3.33,
                            0.0068: 3.33}}
metrics = [{'module' : 'load', 'params' : ['time_total', 'time_COMPUTE_useful', 'energy_COMPUTE_useful', 'energy_total','num_CHECKPOINT_successful', 'num_RESTORE_successful', 'num_CHECKPOINT_failed', 'forward_progress', 'time_off_mean', 'time_off_max', 'time_compute_mean', 'time_unavailable_mean', 'time_unavailable_max', 'time_available_mean', 'time_available_max', 'time_available_min']}]

if __name__ == '__main__':
    result = run_tradeoff_exploration(params, metrics, base_config, settings, mapping_params = [map_params])
    result = pd.DataFrame(result)
    result.to_json("Result.json") #store if we want to use it later without simulating
    
    #%%
    result = pd.read_json("Result.json")
    r = result.copy()
    r = r.rename({'cap.capacitance' : 'cap', 'converter.v_out_enable_treshold_high' : 'vhigh', 'load.forward_progress' : 'forward_progress', 'load.time_unavailable_mean' : 't_unav_mean', 'load.time_unavailable_max' : 't_unav_max', 'load.time_available_mean' : 't_av_mean', 'load.time_available_max' : 't_av_max', 'load.time_available_min' : 't_av_min'}, axis=1)
    res = r[['cap', 'vhigh', 'forward_progress', 't_av_mean','t_av_max', 't_av_min', 't_unav_mean', 't_unav_max', 'load.num_CHECKPOINT_successful']]
   
    res.vhigh = round(res.vhigh,2)
    res['cap_mF'] = res.cap*1e3
    
    # Mark parameter pairs where capacitance is large enough to fit one restore/checkpoint cycle 
    min_c = {3.63 : 0.56, 3.97: 0.56, 4.3: 0.36, 4.61 : 0.26, 4.87: 0.2}
    for v, c in min_c.items():
        res.loc[res.vhigh == v, 'feasible'] = res.loc[res.vhigh == v, 'cap_mF'] >= c

    # Plot all parameter pairs
    fig, axs = plt.subplots(nrows=1, ncols = 2, figsize=(6,2.0), sharex=True)
             
    for v_high in res['vhigh'].sort_values().unique():
        res[res['vhigh'] == v_high].sort_values('cap_mF').plot(x = 'cap_mF', y='forward_progress', ax = axs[1], label=v_high, grid = True, linewidth=0.5, zorder=0,legend=False)
        res[res['vhigh'] == v_high].sort_values('cap_mF').plot(x = 'cap_mF', y='t_unav_mean', ax = axs[0], label=v_high, grid = True, linewidth=0.5,zorder=0,legend=False)
    
    # Plot feasible candidates stronger
    for v_high, line in zip(res['vhigh'].sort_values().unique(),axs[0].get_children()[0:5]):
        res[(res.vhigh == v_high) & (res.t_unav_max < 1)& (res.forward_progress > 0.01) & (res.feasible)].plot(x = 'cap_mF', y='forward_progress', kind='scatter', ax = axs[1], marker = 'x', color=line.get_color(), zorder =1,legend=False,grid = True, s=2)
        res[(res.vhigh == v_high) & (res.t_unav_max < 1)& (res.forward_progress > 0.01) & (res.feasible)].plot(x = 'cap_mF', y='t_unav_mean', kind='scatter', ax = axs[0], marker='x', zorder =1,color=line.get_color(),legend=False,grid = True, s=2)
    
    # Color feasible candidates in grey
    r_candidates = res[(res.t_unav_max <= 1) & (res.forward_progress > 0.01) & (res.feasible)]
    r_candidates.sort_values('forward_progress', ascending=False)[['forward_progress', 't_unav_max']]
   
    y_min = r_candidates.groupby('vhigh').min()[['forward_progress', 'cap_mF']]
    y_max = r_candidates.groupby('vhigh').max()[['forward_progress', 'cap_mF']]
    x = np.concatenate((y_max.cap_mF.values, y_min.cap_mF.values))
    x.sort()
    y_min = [r_candidates[r_candidates.cap_mF == c].forward_progress.min() for c in x]
    y_max = [r_candidates[r_candidates.cap_mF == c].forward_progress.max() for c in x]
    axs[1].fill_between(x,y_max, y_min, color='grey', alpha=0.2,interpolate='True')
    
    y_min = r_candidates.groupby('vhigh').min()[['t_unav_max', 'cap_mF']]
    y_max = r_candidates.groupby('vhigh').max()[['t_unav_max', 'cap_mF']]
    x = np.concatenate((y_max.cap_mF.values, y_min.cap_mF.values))
    x.sort()
    y_min = [r_candidates[r_candidates.cap_mF == c].t_unav_max.min() for c in x]
    y_max = [r_candidates[r_candidates.cap_mF == c].t_unav_max.max() for c in x]
    axs[0].fill_between(x,y_max, y_min, color='grey', alpha=0.2,interpolate='True')
    
    
    # Polish
    titlesize=10
    labelsize=9
    
    h,l = axs[0].get_legend_handles_labels()
    axs[0].legend(h,l, loc='best', title="$V_{High} (V)$",fontsize=9,labelspacing=0.2, columnspacing=0.1, title_fontsize=9, ncol=2)
    axs[1].legend(h,l, loc='best', title="$V_{High} (V)$",fontsize=9,labelspacing=0.2, columnspacing=0.1,title_fontsize=9, ncol=2)
    
    axs[0].set_title("(a) Unavailability $f(C,V_{High})$.", fontsize=titlesize) 
    axs[1].set_title("(b) Forward progress $f(C,V_{High})$.", fontsize=titlesize)
    axs[0].set_xlabel("Capacitance (mF)", fontsize=labelsize, labelpad=0)
    axs[1].set_xlabel("Capacitance (mF)", fontsize=labelsize, labelpad=0)
    axs[0].set_ylabel("$t_{unavailable,max}$ (s)", fontsize=labelsize, labelpad=0)
    axs[1].set_ylabel(r"Forward progress $\alpha$", fontsize=labelsize, labelpad=0)
    axs[0].tick_params(axis='both', which='both', pad=1, labelsize=labelsize)
    axs[1].tick_params(axis='both', which='both', pad=1, labelsize=labelsize)
    fig.subplots_adjust(top=0.87,
                         bottom=0.175,
                         left=0.07,
                         right=0.975,
                         hspace=0.2,
                         wspace=0.25)
    fig.savefig("GameboyVhighC.pdf")
