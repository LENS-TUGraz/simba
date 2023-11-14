# -*- coding: utf-8 -*-
"""
Show impact of capacitance on application performance.

Simulate Botoks for different capacitance configurations (sweep) and at certain constant input currents
for 10 seconds and derive metrics accordingly.

Plot i) Amount of wasted energy (%), ii) average time turned off, and iii) number of sent packets as a function of capacitance.
Add datapoints of experimental evaluation to plot and derive simulation error.
"""

from Simba import Simulation, cap_factory, harvester_factory
import pandas as pd
import numpy as np
import matplotlib.lines as mlines
from matplotlib.patches import Patch
import matplotlib.pyplot as plt
import datetime
import botoks_data_handler
import os
# Import Botoks module configurations for simulation
from Botoks import harvest_config, capacitor_config, converter_config, load_config_burn, cap_values, color_map

PLOT_EXPERIMENTAL_DATAPOINTS = True
PLOT = False #For debugging, plot each experiment over time -- avoid


# %% Perform simulations for several configurations and retrieve statistics

# Specify which experiments we make
SIM_TIME = 10 #We simulate for 10 seconds (we also measured for 10 seconds)
currents = [100e-6, 400e-6, 1000e-6]
capacitances = np.linspace(10e-6, 120e-6, 50)
capacitances = np.append(capacitances, [22e-6, 47e-6, 100e-6])
capacitor_config['settings']['v_initial'] = 3.1
start = datetime.datetime.now()

#Create simulation environment
sim = Simulation(capacitor_config, harvest_config, converter_config, load_config_burn)
sim.max_step_size = 1e-3

stats = pd.DataFrame()
# We iterate over currents and capacitors and update simulator modules accordingly
for current in currents:
    
    harvest_config['settings']['i_high'] = current
    sim.harvester = harvester_factory(harvest_config, sim.min_step_size)
    
    for cap in capacitances:
        
        capacitor_config['settings']['capacitance'] = cap
        sim.cap = cap_factory(capacitor_config, sim.min_step_size)
        
        # Run simulation and retrieve/store statistics
        print(f"Simulate with C = {cap} and I = {current}")
        sim.run(until = SIM_TIME) 
        
        c_stats = pd.DataFrame(sim.load.get_log_stats(), index=[0])
        c_stats['cap'] = int(cap * 1e6)
        c_stats['current'] = current
        
        stats = pd.concat([stats, c_stats])
        
        if PLOT: #Plot over time       
            
            load_log = sim.load.get_log()
            harvest_log = sim.harvester.get_log()
            cap_log = sim.cap.get_log()
                
            fig, axs = plt.subplots(nrows=3, sharex=True, gridspec_kw={'height_ratios': [2, 2, 1]})
            
            #Plot capacitor voltage and harvesting/load currents over time
            load_log.plot(x='time', y='v_out', ax=axs[0], color='lightgrey', label = 'V-Load')
            cap_log.plot(x='time', y='voltage', ax=axs[0], color='black', label = 'V-Cap')
            axs[0].set_ylabel("Voltage (V)")
            axs[0].axhline(y=converter_config['settings']['v_high'], color='grey') #Voltage tresholds
            axs[0].axhline(y=converter_config['settings']['v_low'], color='grey') #voltage tresholds
            axs[0].set_xlabel("Time (s)")
            
            #Plot incoming and outgoing currents over time
            load_log.plot(x='time', y='i_out', ax=axs[1], color='black', label = 'i_load', drawstyle='steps-post')
            harvest_log.plot(x='time', y='i_in', ax=axs[1], color='grey', label = 'i_in', drawstyle='steps-post')
            axs[1].set_ylabel("Current (A)")
            #harvest_log.plot(x='time', y='i_max', ax=axs[1], color='light_grey', label = 'i_in_max', drawstyle='steps-post')
            
            #Color trace according to states
            legend_elements = []
            for state, color in color_map.items():
                states = load_log[load_log.state == state]
                #axs[0].barh([min(load_log.v_out.min(), cap_log.voltage.min())]*len(states),  states.dt, left = states.time, color=color, alpha=0.2, align = 'edge', height = max(load_log.v_out.max(), cap_log.voltage.max()))
                #axs[1].barh([min(load_log.i_out.min(), harvest_log.i_in.min())]*len(states), states.dt, left = states.time, color=color, alpha=0.2, align = 'edge', height =  max(load_log.i_out.max(), harvest_log.i_in.max()))
                axs[2].barh([0]*len(states), states.dt, left = states.time, color=color, alpha=0.2)
                legend_elements.append(Patch(facecolor=color, edgecolor=color, label=state, alpha=0.2))
            
            axs[2].legend(handles=legend_elements, loc='lower center', ncol = len(legend_elements))
            axs[2].set_xlabel("Time (s)")
            axs[2].set_yticks([], [])
            s =  sim.load.get_log_stats()
            
            useful_energy = s['energy_useful_SENSE'] * s['num_SEND_successful'] / s['num_SENSE_successful'] + s['energy_useful_SEND']
            useful_energy_rel = useful_energy / (s['energy_SENSE'] + s['energy_SEND'] + s['energy_SLEEP'])
            fig.suptitle(f"Transmissions: {s['num_SEND_successful']} successful / {s['num_SEND_failed']} failed\n" + \
                          f"Mean time between samples: {c_stats['time_between_samples_mean'].iloc[0]:.6f}\n" + \
                          f"Energy useful (absolute / rel. to total energy) : {useful_energy:.6f} / {useful_energy_rel:.6f}")
        

stats = stats.sort_values('cap')

print(f"Total sim time: {datetime.datetime.now() - start}")

#%% Load data from experiments and perform simulations for exact same configuration

if PLOT_EXPERIMENTAL_DATAPOINTS:
        
    # Select data points to load/simulate
    currents = [100, 400, 1000]
    capacitances = [10, 22, 47, 100]
    sim.max_step_size = 1e-4
    
    measurement_path = "../../Artifacts/Botoks/ExtractedData/DataCapsizesJson/digital"
    measured_stats = pd.DataFrame()
    errors = pd.DataFrame()
    
    if os.path.exists(measurement_path):
        for current in currents:
            for cap in capacitances:
                # Load mesaured data and compute statistics
                measurement_filename = f"result_burn_cap{cap}_{current}"
                data_measured_dig = botoks_data_handler.load_botoks_trace_digital(measurement_path, measurement_filename)
                m_stats = botoks_data_handler.get_botoks_stats(data_measured_dig)
                m_stats['current'] = current
                m_stats['cap'] = int(cap_values[cap] * 1e6)
                measured_stats = pd.concat([measured_stats, pd.DataFrame(m_stats, index=[0])], ignore_index=True)
                
                #Perform simulation with same configuration and get statistics
                harvest_config['settings']['i_high'] = current * 1e-6
                capacitor_config['settings']['capacitance'] = cap_values[cap]
                sim.harvester = harvester_factory(harvest_config, sim.min_step_size)
                sim.cap = cap_factory(capacitor_config,sim.min_step_size)
                sim.run(until = SIM_TIME) 
                c_stats = sim.load.get_log_stats()
                
                # Compute simulation errors 
                error = {}
                error['cap'] = int(cap * 1e6)
                error['current'] = current
                if m_stats['MeanTimeOff'] != 0:
                    error['error_off_time'] = (c_stats['time_off_mean'] - m_stats['MeanTimeOff'])/ m_stats['MeanTimeOff']
                else:
                    error['error_off_time'] = None
                    
                if m_stats['MeanTimeSample'] != 0:
                    error['error_sample_time'] = (c_stats['time_between_SEND_mean'] - m_stats['MeanTimeSample'])/ m_stats['MeanTimeSample']
                else:
                    error['error_sample_time'] = None
                        
                    
                if m_stats['NumSamples'] != 0:
                    error['error_num_packets'] = (c_stats['num_success_SEND'] - m_stats['NumSamples'])/ m_stats['NumSamples']
                else:
                    error['error_num_packets'] = None
                errors = pd.concat([errors, pd.DataFrame(error, index=[0])], ignore_index=True)
    
        #%%  Print simulation errors
        print("Simulation errors:")
        print(f"Mean off time: {abs(errors).mean().error_off_time:.3f} (mean) / {abs(errors).min().error_off_time:.3f} (min) / {abs(errors).max().error_off_time:.3f} (max)")
        print(f"Num packets: {abs(errors).mean().error_num_packets:.3f} (mean)/ {abs(errors).min().error_num_packets:.3f}  (min) / {abs(errors).max().error_num_packets:.3f} (max)")
        print(f"Mean sample time: {abs(errors).mean().error_sample_time:.3f} (mean)/ {abs(errors).min().error_sample_time:.3f}  (min) / {abs(errors).max().error_sample_time:.3f} (max)")
    
    else:
        print("Error: could not find experimental data files. Skipped in plots.")
        PLOT_EXPERIMENTAL_DATAPOINTS = False

#%% Compute additional statistics and plot both simulated and measured data

stats['energy_wasted'] = stats['energy_BURN']
stats['energy_wasted_rel'] = 100 * (stats['energy_wasted'] / (stats['energy_INIT'] + stats['energy_SENSE'] + stats['energy_SEND'] + stats['energy_BURN']))
stats_plot = stats.replace(0, np.nan)

# Define proper colors/lines that work also in greyscale and for color-blind people
current_colors = ['#377eb8', '#4daf4a', '#999999', '#a65628']
current_linestyles = ['solid', 'dashed', 'dashdot', 'dotted']

titlesize=10
labelsize=9

fig, axs = plt.subplots(nrows = 3, sharex = True, figsize=(6,4))

for current, col, line in zip(stats_plot.sort_values('current').current.unique(), current_colors, current_linestyles):
    stats_plot[stats_plot.current == current].plot(x='cap', y='energy_wasted_rel', ax=axs[0], label=current*1e6, color=col, linestyle=line, legend=False)
    axs[0].set_title("(a) Energy wasted in $BURN$ state.", fontsize=titlesize)
    axs[0].set_ylabel('$E_{wasted}$/$E_{total}$ (%)', fontsize=labelsize, labelpad=0)
    axs[0].tick_params(axis='y', which='major', pad=2, labelsize=labelsize)
    
    # stats_plot[stats_plot.current == current].plot(x='cap', y='time_off_mean', ax=axs[1], label=current*1e6, color=col, linestyle=line, legend=False)
    # axs[1].set_title("(b) Average time spent in $OFF$ state.", fontsize=titlesize)
    # axs[1].set_ylabel('$avg(T_{off})$ (s)', fontsize=labelsize, labelpad=0)
    # axs[1].tick_params(axis='y', which='major', pad=2, labelsize=labelsize)
    
    stats_plot[stats_plot.current == current].plot(x='cap', y='time_between_SEND_mean', ax=axs[1], grid=True, label=current*1e6, color=col, linestyle=line, legend=False)
    axs[1].set_title("(b) Average time between two samples.", fontsize=titlesize)
    axs[1].set_ylabel('$T_{Sample,mean}$ (s)', fontsize=labelsize, labelpad=0)
    axs[1].tick_params(axis='y', which='major', pad=2, labelsize=labelsize)
    
    stats_plot[stats_plot.current == current].plot(x='cap', y='num_success_SEND', ax=axs[2], grid=True, label=current*1e6, color=col, linestyle=line, legend=False)
    axs[2].set_title("(c) Number of successful packets.", fontsize=titlesize)
    axs[2].set_ylabel('#Packets', fontsize=labelsize, labelpad=0)
    axs[2].tick_params(axis='y', which='major', pad=2, labelsize=labelsize)
    
    # Add points of measured data
    if PLOT_EXPERIMENTAL_DATAPOINTS:
        measured_stats[measured_stats.current == int(current * 1e6)].plot(x='cap', y='MeanTimeSample', ax=axs[1], linestyle='None', marker='x',label=current*1e6, color=col, legend=False)
        measured_stats[measured_stats.current == int(current * 1e6)].plot(x='cap', y='NumSamples', ax=axs[2], linestyle="None" , marker='x',label=current*1e6, color=col, legend=False)

# Add legends to plots
h, l = axs[0].get_legend_handles_labels()
l = ["$I_H$=" + label.replace(".0", "\u03bcA") for label in l]
fig.legend(handles=h, labels=l, loc='upper center', ncol = len(l), fontsize=labelsize, labelspacing=0.2, handletextpad=0.2)
if PLOT_EXPERIMENTAL_DATAPOINTS:
    axs[1].legend(handles=[mlines.Line2D([], [], color='black', marker='x', linestyle='None', label='Measured values')],  fontsize=labelsize, handletextpad=0.2)
    axs[2].legend(handles=[mlines.Line2D([], [], color='black', marker='x', linestyle='None', label='Measured values')], fontsize=labelsize, handletextpad=0.2)

# Polish
for ax in axs:
    ax.grid(True)
axs[2].set_xlabel("Capacitance (\u03bcF)", fontsize=labelsize)
axs[2].tick_params(axis='x', which='major', pad=2, labelsize=labelsize)
axs[0].set_ylim([15, 95])
axs[2].set_xlim([0, stats_plot.cap.max() + 5])
fig.align_ylabels(axs)
fig.subplots_adjust(top=0.86, bottom=0.12, left=0.1, right=0.98, hspace=0.39, wspace=0.2)
fig.savefig("BotoksCapsizes.pdf")

#%% Print some statistics/comparisons of specific capacitor values (e.g., original = 100uF, improvemnts when choosing 47uF or 22uF)
input_current = 0.001
print_stats = stats[(stats.current == input_current) & stats.cap.isin([100,47,22,10])]
print(print_stats[['cap', 'time_between_SEND_mean', 'energy_wasted_rel', 'num_success_SEND']])