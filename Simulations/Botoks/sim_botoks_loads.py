# -*- coding: utf-8 -*-
"""
Simulate two different applications on intermittently powered Botoks platform and show energy efficiency/on times etc.
In both cases, the Botoks platform should perform a simple send and sensing application (Sense and immediately send afterwards).

In the first case, the platform goes to sleep mode after transmission, remains there for x seconds and tries to sense/send afterwards.
In the second case, the platform 'burns' its remaining energy and waits until the capacitor recharges to perform the next sense/send cycle.

Plot performance metrics for different input currents and plot also results from experiments
"""

from Simba import Simulation, harvester_factory, load_factory
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.lines as mlines
import botoks_data_handler
import os

# Import Botoks module configurations for simulation
from Botoks import harvest_config, capacitor_config, converter_config,  load_config_burn, load_config_loop

PLOT_EXPERIMENTAL_DATAPOINTS = True

#%%

# Specify which experiments we make
SIM_TIME = 10 #We simulate for 10 seconds (we also measured for 10 seconds)
currents = [100, 200, 400, 600, 1000, 1500]
loads = [load_config_burn, load_config_loop]
capacitor_config['settings']['capacitance'] = 110e-6 #Original Botoks capacitance (=100uF), real, measured capacitance = 110uF


# Create simulation environment
sim = Simulation(capacitor_config, harvest_config, converter_config, load_config_loop)
sim.max_step_size = 1e-5

stats = pd.DataFrame()
# We iterate over loads and currents and update simulator modules accordingly
for load in loads:

    sim.load = load_factory(load, sim.min_step_size)
    for current in currents:
        
        harvest_config['settings']['i_high'] = current * 1e-6
        sim.harvester = harvester_factory(harvest_config, sim.min_step_size)
        
        # Run simulation and collect statistics
        sim.run(until = SIM_TIME) 
        
        c_stats = pd.DataFrame(sim.load.get_log_stats(True), index=[0])
        c_stats['current'] = int(current)
        c_stats['load'] = load['name']
        
        stats = pd.concat([stats, c_stats])
        
        
            
stats = stats.reset_index(drop=True)
#%% Compute energy statistics
#Compute wasted energy depending on load type
#1) For 'burn' applications the wasted energy is either the energy n burn state (after successful sending) or everything until the burning (if sending was not successful)
stats.loc[stats.load.str.contains('Burn'), 'energy_wasted_total'] = stats.loc[stats.load.str.contains('Burn'), :].apply(lambda x : x.energy_BURN if x.energy_BURN != 0 else x.energy_INIT + x.energy_SEND + x.energy_SENSE, axis=1)
#2) For 'loop' applications, we need to sum up everything that did not lead to successful transmission
amount_useless_sensing_and_init = stats.loc[stats.load.str.contains('Loop'), 'num_fail_SEND'] / (stats.loc[stats.load.str.contains('Loop'),'num_success_SEND'] + stats.loc[stats.load.str.contains('Loop'), 'num_fail_SEND'])
amount_useless_init = stats.loc[stats.load.str.contains('Loop'),'num_fail_SENSE'] / (stats.loc[stats.load.str.contains('Loop'),'num_success_SENSE'] + stats.loc[stats.load.str.contains('Loop'),'num_fail_SENSE'])
stats.loc[stats.load.str.contains('Loop'), 'energy_wasted_total'] = stats.loc[stats.load.str.contains('Loop'), 'energy_wasted_SEND'] + stats.loc[stats.load.str.contains('Loop'), 'energy_wasted_INIT'] + stats.loc[stats.load.str.contains('Loop'), 'energy_wasted_SENSE']
stats.loc[stats.load.str.contains('Loop'), 'energy_wasted_total'] += amount_useless_sensing_and_init * (stats.loc[stats.load.str.contains('Loop'), 'energy_SENSE']  + stats.loc[stats.load.str.contains('Loop'),  'energy_INIT'])
stats.loc[stats.load.str.contains('Loop'), 'energy_wasted_total'] += amount_useless_init * stats.loc[stats.load.str.contains('Loop'), 'energy_INIT']

#Wasted energy in percent = total wasted energy/total energy
stats.loc[stats.load.str.contains('Burn'), 'energy_wasted_rel'] = stats.loc[stats.load.str.contains('Burn'), 'energy_wasted_total'] / (stats.loc[stats.load.str.contains('Burn'), 'energy_SENSE'] + stats.loc[stats.load.str.contains('Burn'),'energy_SEND'] + stats.loc[stats.load.str.contains('Burn'),'energy_INIT'] + stats.loc[stats.load.str.contains('Burn'),'energy_BURN'])
stats.loc[stats.load.str.contains('Loop'), 'energy_wasted_rel'] = stats.loc[stats.load.str.contains('Loop'), 'energy_wasted_total'] / (stats.loc[stats.load.str.contains('Loop'), 'energy_SENSE'] + stats.loc[stats.load.str.contains('Loop'),'energy_SEND'] + stats.loc[stats.load.str.contains('Loop'),'energy_INIT'])

#%% Load data from experiments 

if PLOT_EXPERIMENTAL_DATAPOINTS:
    
    # Name to filename-index
    load_names= {'Load_Burn' : 'burn',
                 'Load_Loop' : 'loop'}
    
    measurement_path = "../../Artifacts/Botoks/ExtractedData/DataLoadJson"
    
    errors = pd.DataFrame()
    measured_stats = pd.DataFrame()
    
    if os.path.exists(measurement_path):
    
        # We get all the measurement data we have for this configuration
        for load in loads:
            for current in currents:
                try:
                    
                    # Load measurement data and compute statistics
                    measurement_filename = f"result_{load_names[load['name']]}_cap100_{current}"
                    data_measured_dig = botoks_data_handler.load_botoks_trace_digital(measurement_path, measurement_filename)
                    m_stats = botoks_data_handler.get_botoks_stats(data_measured_dig)
                    m_stats['current'] = current
                    m_stats['load'] = load['name']
                    measured_stats = pd.concat([measured_stats, pd.DataFrame(m_stats, index=[0])], ignore_index=True)
                    
                    #Compute simulation errors   
                    error = {}
                    error['current'] = current
                    error['load'] = load['name']
                    
                    s_stats = stats[(stats.current == current) & (stats.load == load['name'])].iloc[0] #Get simulation result with same configuration
                    if m_stats['MeanTimeSample'] != 0:
                        error['error_sample_time'] = (s_stats['time_between_SEND_mean'] - m_stats['MeanTimeSample'])/ m_stats['MeanTimeSample']
                        
                        error['error_sample_time_max'] = (s_stats['time_between_SEND_max'] - m_stats['MaxTimeSample'])/ m_stats['MaxTimeSample']
                    else:
                        error['error_sample_time'] = None
                        error['error_sample_time_max'] = None
                        
                    if m_stats['NumSamples'] != 0:
                        error['error_num_packets'] = (s_stats['num_success_SEND'] - m_stats['NumSamples'])/ m_stats['NumSamples']
                    else:
                        error['error_num_packets'] = None
                    errors = pd.concat([errors, pd.DataFrame(error, index=[0])], ignore_index=True)
                except FileNotFoundError:
                    error['current'] = current
                    error['load'] = load['name']
                    errors = pd.concat([errors, pd.DataFrame(error, index=[0])], ignore_index=True)
                    m_stats = {}
                    m_stats['current'] = current
                    m_stats['load'] = load['name']
                    measured_stats = pd.concat([measured_stats, pd.DataFrame(m_stats, index=[0])], ignore_index=True)
                
        # Print simulation errors for each load type (and overall errors)
        
        errors_loop = errors[errors.load == 'Load_Loop'][['error_sample_time', 'error_num_packets', 'error_sample_time_max']]
        print("Simulation errors loop:")
        print(f"Mean sample time: {abs(errors_loop).mean().error_sample_time:.3f} (mean) / {abs(errors_loop).min().error_sample_time:.3f} (min) / {abs(errors_loop).max().error_sample_time:.3f} (max)")
        print(f"Max sample time: {abs(errors_loop).mean().error_sample_time_max:.3f} (mean) / {abs(errors_loop).min().error_sample_time_max:.3f} (min) / {abs(errors_loop).max().error_sample_time_max:.3f} (max)")
        print(f"Num packets: {abs(errors_loop).mean().error_num_packets:.3f} (mean)/ {abs(errors_loop).min().error_num_packets:.3f}  (min) / {abs(errors_loop).max().error_num_packets:.3f} (max)")
        print("Simulation errors burn:")
        
        errors_burn = errors[errors.load == 'Load_Burn'][['error_sample_time', 'error_num_packets', 'error_sample_time_max']]
        print("Simulation errors burn:")
        print(f"Mean sample time: {abs(errors_burn).mean().error_sample_time:.3f} (mean) / {abs(errors_burn).min().error_sample_time:.3f} (min) / {abs(errors_burn).max().error_sample_time:.3f} (max)")
        print(f"Max sample time: {abs(errors_burn).mean().error_sample_time_max:.3f} (mean) / {abs(errors_burn).min().error_sample_time_max:.3f} (min) / {abs(errors_burn).max().error_sample_time_max:.3f} (max)")
        print(f"Num packets: {abs(errors_burn).mean().error_num_packets:.3f} (mean)/ {abs(errors_burn).min().error_num_packets:.3f}  (min) / {abs(errors_burn).max().error_num_packets:.3f} (max)")
        
        errors_print = errors[['error_sample_time', 'error_num_packets', 'error_sample_time_max']]
        print("Simulation errors total:")
        print(f"Mean sample time: {abs(errors_print).mean().error_sample_time:.3f} (mean) / {abs(errors_print).min().error_sample_time:.3f} (min) / {abs(errors_print).max().error_sample_time:.3f} (max)")
        print(f"Max sample time: {abs(errors_print).mean().error_sample_time_max:.3f} (mean) / {abs(errors_print).min().error_sample_time_max:.3f} (min) / {abs(errors_print).max().error_sample_time_max:.3f} (max)")
        print(f"Num packets: {abs(errors_print).mean().error_num_packets:.3f} (mean)/ {abs(errors_print).min().error_num_packets:.3f}  (min) / {abs(errors_print).max().error_num_packets:.3f} (max)")

    else:
        print("Error: could not find experimental data files. Skipped in plots.")
        PLOT_EXPERIMENTAL_DATAPOINTS = False

#%% Plot statistics of all configurations

colors = ['#377eb8', '#4daf4a']
hatches = ['//', '/']
titlesize=10
labelsize=9

fig, axs = plt.subplots(nrows = 3, sharex = True, figsize=(3.5,3.1))

stats.pivot(index="current", columns="load", values="energy_wasted_rel").plot(kind='bar', ax=axs[0], legend=False, color=colors)
#axs[0].set_title('Wasted energy (%)', fontsize=labelsize)
axs[0].set_ylabel("$\\frac{E_{Wasted}}{E_{Total}}$(%)", fontsize=labelsize+1, labelpad=2)
axs[0].tick_params(axis='both', which='major', pad=2, labelsize=labelsize)

# df.pivot(index="current", columns="load", values="time_between_SEND_mean").plot(kind='bar', ax=axs[1], legend=False, color=colors)
# axs[1].set_title('Time between samples mean (s)', fontsize=labelsize)
# axs[1].set_ylabel('avg($T_{Sample}$)\n(s)', fontsize=labelsize)

stats.pivot(index="current", columns="load", values="time_between_SEND_max").plot(kind='bar', ax=axs[1], legend=False, color=colors)
#axs[1].set_title('Maximum time between samples (s)', fontsize=labelsize)
axs[1].set_ylabel('$T_{Sample,max}$(s)', fontsize=labelsize, labelpad=2)
axs[1].tick_params(axis='both', which='major', pad=2, labelsize=labelsize)

stats.pivot(index="current", columns="load", values="num_success_SEND").plot(kind='bar', ax=axs[2], legend=False, color=colors)
#axs[2].set_title('#Sucessful packets', fontsize=labelsize)
axs[2].set_ylabel('#Packets', fontsize=labelsize, labelpad=2)
axs[2].tick_params(axis='both', which='major', pad=2, labelsize=labelsize)

if PLOT_EXPERIMENTAL_DATAPOINTS:
    # Add points for measured data
    for l, offset in zip(measured_stats.load.unique(), [-0.125, 0.125]):
        
        ticks = [t + offset for t in axs[2].get_xticks()]
        #axs[1].plot(ticks, df_m[df_m.load == l].sort_values('current').reset_index(drop=True)['MeanTimeSample'], marker='x', linestyle='None', color='black')    
        axs[1].plot(ticks, measured_stats[measured_stats.load == l].sort_values('current').reset_index(drop=True)['MaxTimeSample'].values, marker='x', linestyle='None', color='black')
        axs[2].plot(ticks, measured_stats[measured_stats.load == l].sort_values('current').reset_index(drop=True)['NumSamples'].values, marker='x', linestyle='None', color='black')

# Add legend
h, l = axs[2].get_legend_handles_labels()
fig.legend(h,["\'BURN\'", "\'LOOP\'"], ncol=2, loc='lower center', fontsize=labelsize)
if PLOT_EXPERIMENTAL_DATAPOINTS:
    axs[1].legend(handles=[mlines.Line2D([], [], color='black', marker='x', linestyle='None', label='Measured values')],  fontsize=labelsize, handletextpad=0.2)
    axs[2].legend(handles=[mlines.Line2D([], [], color='black', marker='x', linestyle='None', label='Measured values')], fontsize=labelsize, handletextpad=0.2)

# Polish
fig.suptitle("(a) Application with $t_{Sense} < t_{Send}$", fontsize=titlesize, y=0.98)
axs[2].set_xlabel("Input current $I_H$ (\u03bcA)", fontsize=labelsize, labelpad = 0)
axs[2].set_xticklabels(axs[2].get_xticklabels(), rotation=0)

for ax in axs:
    ax.grid(True)

fig.align_ylabels(axs)
fig.subplots_adjust(top=0.92,
bottom=0.225,
left=0.21,
right=0.96,
hspace=0.4,
wspace=0.19)

fig.savefig('BotoksLoads.pdf')


#%% Print differences in percent
loop_stats = stats[stats.load.str.contains('Loop')][['current', 'load', 'time_between_SEND_max', 'num_success_SEND']].reset_index(drop=True)
burn_stats = stats[stats.load.str.contains('Burn')][['current', 'load', 'time_between_SEND_max', 'num_success_SEND']].reset_index(drop=True)

#reset index, so that we can subtract each others values
loop_stats = loop_stats.reset_index(drop=True)
burn_stats = burn_stats.reset_index(drop=True)

burn_stats['DiffMaxTime'] = (burn_stats.loc[:,'time_between_SEND_max'] - loop_stats.loc[:,'time_between_SEND_max'])/burn_stats.loc[:,'time_between_SEND_max']
burn_stats['DiffNumSamples'] = (burn_stats.loc[:,'num_success_SEND'] - loop_stats.loc[:,'num_success_SEND'])/burn_stats.loc[:,'num_success_SEND']

print("Difference (%) between burning and looping application.")
print(burn_stats[['DiffMaxTime', 'DiffNumSamples']])
