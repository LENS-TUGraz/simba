# -*- coding: utf-8 -*-
"""
Simulate different capacitor/threshold combinations for 
(directly coupled) Botoks using a AM1417 solar panel (pre-recorded IV curve).

- Plot ON/OFF times, amount of harvested energy and number of samples.
- In these scenarios, lower capacitances are not always beneficial, as 
higher voltage tresholds are required and the solar panal might not be 
able to deliver them.
"""

from Simba import Simulation, cap_factory, harvester_factory, converter_factory
import pandas as pd
import matplotlib.pyplot as plt
import math
import matplotlib.lines as mlines
import os
import botoks_data_handler

# Import Botoks module configurations for simulation
from Botoks import cap_values, load_config_burn, capacitor_config, converter_config, harvest_config_solar

PLOT_EXPERIMENTAL_DATAPOINTS = True

#%% Create voltage/capacitor pairs with same energy budget as basic configuration (C = 47e-6, Vhigh = 3.1V)

# Basic configuration -- what we start out with
cap = 47e-6
v_low = 2.4 #v_low is fixed
v_high = 3.1

energy_budget = cap * ( v_high ** 2 - v_low ** 2) / 2

new_caps = [22e-6, 33e-6, 100e-6] # Other capacitance configurations
cap_voltage_pairs = [(cap, v_high)]

for c_new in new_caps: #for each c, compute the upper threshold that yields the same energy budget
    v_high_new = math.sqrt(2*energy_budget/c_new + v_low**2)
    cap_voltage_pairs.append((c_new, round(v_high_new,2)))

print(cap_voltage_pairs)
cap_voltage_pairs = {(22e-6, 3.65), (47e-6, 3.05), (100e-6, 2.6)}#, (33e-6, 3.35)}
#%% Simulate Botoks for each voltage/capacitance pair and retrieve statistics
SIM_TIME = 10   #in seconds
load = 'burn'   #type of application running (loop or burn)
panels = ['AM1417'] #Select types of solar panels 
lux_values = [20000, 18000, 15000, 13000] #Select illuminance values

#%%
## Plot stats for different threshold configurations using Botok's original solar panel
## Plot also PV-curve to explain the behavior

panel = 'AM1417'

#%% Get simulation data

# Create simulation environment

harvest_config_solar['settings']['log'] = True
sim = Simulation(capacitor_config, harvest_config_solar, converter_config, load_config_burn)
sim.max_step_size = 1e-3

stats_solar = pd.DataFrame()

for lux in lux_values:

    harvest_config_solar['settings']['file'] = f'{panel}_lux{lux}.json'
    sim.harvester = harvester_factory(harvest_config_solar, sim.min_step_size)
    
    # Let's explore different threshold configs
    for c_v in cap_voltage_pairs:
            
        cap = c_v[0]
        voltage = c_v[1]
        
        capacitor_config['settings']['capacitance'] = cap_values[int(cap*1e6)] if int(cap*1e6) in cap_values else cap
        sim.cap = cap_factory(capacitor_config, sim.min_step_size)
        
        converter_config['settings']['v_high'] = voltage
        sim.converter = converter_factory(converter_config, sim.min_step_size)
        
        print(f"Simulate with C = {cap} and V_high = {voltage}")
        sim.run(until = SIM_TIME) 
            
        #Get stats from load and harvester and store them
        c_stats = pd.DataFrame(sim.load.get_log_stats(), index=[0])
        c_stats['cap'] = int(cap * 1e6)
        c_stats['v_high'] = voltage
        c_stats['lux'] = lux
        c_stats['panel'] = panel
        c_stats['energy_harvested'] = sim.harvester.get_log_stats(False)['energy_total']
        c_stats['max_energy_harvested'] = sim.harvester.get_log_stats(False)['energy_max']
        
        stats_solar = pd.concat([stats_solar, c_stats])
                        
#%% Load measurement data
if PLOT_EXPERIMENTAL_DATAPOINTS:
    capacitances = [22, 47, 100]
    
    measured_stats = pd.DataFrame()
    errors = pd.DataFrame()
    
    measurement_path = f"../../Artifacts/Botoks/ExtractedData/DataThresholdsJson/{panel}/digital"
    
    if os.path.exists(measurement_path): 
        for lux in lux_values:
            for cap in capacitances:
                measurement_filename = f"result_burn_cap{cap}_lux{lux}"
                #Load mesaured data
                data_measured_dig = botoks_data_handler.load_botoks_trace_digital(measurement_path, measurement_filename)
                m_stats = botoks_data_handler.get_botoks_stats(data_measured_dig)
                
                m_stats['lux'] = lux
                m_stats['cap'] = cap
                m_stats['panel'] = panel
        
                
                #Compute simulation errors   
                error = {}
                error['lux'] = lux
                error['panel'] = panel
                error['cap'] = cap
                
                s_stats = stats_solar[(stats_solar.lux == lux) & (stats_solar.cap == cap) & (stats_solar.panel == panel)].iloc[0] #Get simulation result with same configuration
                if m_stats['MeanTimeSample'] != 0:
                    error['error_sample_time'] = abs((s_stats['time_between_SEND_mean'] - m_stats['MeanTimeSample'])/ m_stats['MeanTimeSample'])
                    error['error_sample_time_max'] = abs((s_stats['time_between_SEND_max'] - m_stats['MaxTimeSample'])/ m_stats['MaxTimeSample'])
                else:
                    error['error_sample_time'] = 0
                    error['error_sample_time_max'] = 0
                    
                    
                if m_stats['NumSamples'] != 0:
                    error['error_num_packets'] = abs((s_stats['num_success_SEND'] - m_stats['NumSamples'])/ m_stats['NumSamples'])
                else:
                    error['error_num_packets'] = 0
                errors = pd.concat([errors, pd.DataFrame(error, index=[0])], ignore_index=True)
                m_stats = pd.DataFrame(m_stats, index=[0])
                measured_stats = pd.concat([measured_stats, m_stats], ignore_index=True)

        # Print simulation errors for each solar panel type (and overall errors)
        
        errors_print = errors[errors.error_num_packets < 1][['error_sample_time', 'error_num_packets', 'error_sample_time_max']]
        print("Simulation errors total:")
        print(f"Mean sample time: {abs(errors_print).mean().error_sample_time:.3f} (mean) / {abs(errors_print).min().error_sample_time:.3f} (min) / {abs(errors_print).max().error_sample_time:.3f} (max)")
        print(f"Max sample time: {abs(errors_print).mean().error_sample_time_max:.3f} (mean) / {abs(errors_print).min().error_sample_time_max:.3f} (min) / {abs(errors_print).max().error_sample_time_max:.3f} (max)")
        print(f"Num packets: {abs(errors_print).mean().error_num_packets:.3f} (mean)/ {abs(errors_print).min().error_num_packets:.3f}  (min) / {abs(errors_print).max().error_num_packets:.3f} (max)")

    else:
        print("Error: could not find experimental data files. Skipped in plots.")
        PLOT_EXPERIMENTAL_DATAPOINTS = False  

#%% Plot results from simulations

fig, axs = plt.subplots(ncols = 1, nrows = 2, figsize=(3,2.7))
colors = ['#377eb8', '#4daf4a', '#999999', '#a65628']
titlesize=10
labelsize=9

stats_solar = stats_solar.sort_values('cap')
stats_solar['energy_harvested_mj'] = stats_solar['energy_harvested'] * 1000 


panel_plots = {'KXOB25-02-X8F' : [22, 47, 100, 200],
               'AM1417' : [47, 100, 200]}

#stats_solar[(stats_solar.panel == panel) & (stats_solar.cap.isin(panel_plots[panel]))].pivot(["cap", "v_high"], "lux", "time_off_mean").plot(kind='bar', ax=axs[0], color=colors, legend = False,zorder=1)
stats_solar[(stats_solar.panel == panel)].pivot(index=["cap", "v_high"], columns="lux", values="num_success_SEND").plot(kind='bar', ax=axs[0], ylabel='# Packets', color=colors, legend = False,zorder=1)
stats_solar[(stats_solar.panel == panel)].pivot(index=["cap", "v_high"], columns="lux", values="energy_harvested_mj").plot(kind='bar', ax=axs[1], ylabel='$E_{Harvested}$ (J)', color=colors, legend = False, zorder=1)

if PLOT_EXPERIMENTAL_DATAPOINTS:    
    df_m = measured_stats[(measured_stats.panel == panel) & (measured_stats.cap.isin(panel_plots[panel]))].sort_values('lux')
    # Add points for measured data
    for l, offset in zip(df_m.lux.unique(), [-3/16, -1/16, 1/16, 3/16]):
    
        ticks = [t + offset for t in axs[0].get_xticks()[1:]]
        axs[0].plot(ticks, df_m[df_m.lux == l].sort_values('cap').reset_index(drop=True)['NumSamples'].values, marker='x', linestyle='None', color='black')    
        #axs[1].plot(ticks, measured_stats[measured_stats.load == l].sort_values('current').reset_index(drop=True)['MaxTimeSample'], marker='x', linestyle='None', color='black')
        #axs[1].plot(ticks, df_m[df_m.lux == l].sort_values('cap').reset_index(drop=True)['NumSamples'], marker='x', linestyle='None', color='black')


axs[0].set_ylabel('# Packets',fontsize=labelsize, labelpad=0)
axs[1].set_ylabel('$E_{Harvested}$ (mJ)',fontsize=labelsize, labelpad=0)

axs[0].tick_params(axis='y', which='major', pad=2, labelsize=labelsize)
axs[1].tick_params(axis='y', which='major', pad=2, labelsize=labelsize)

# Plot maximum amount of harvestable energy as lines in corresponding colors
lines_handles = []
# lines_handles.append(axs[1].axhline(y=stats_solar[(stats_solar.lux == 13000) &(stats_solar.panel == panel)].max_energy_harvested.iloc[0]*1000, color=colors[0],  linestyle='--'))
# lines_handles.append(axs[1].axhline(y=stats_solar[(stats_solar.lux == 15000) &(stats_solar.panel == panel)].max_energy_harvested.iloc[0]*1000, color=colors[1], linestyle='--'))
# lines_handles.append(axs[1].axhline(y=stats_solar[(stats_solar.lux == 18000) &(stats_solar.panel == panel)].max_energy_harvested.iloc[0]*1000, color=colors[2], linestyle='--'))
lines_handles.append(axs[1].axhline(y=stats_solar[(stats_solar.lux == 20000) &(stats_solar.panel == panel)].max_energy_harvested.iloc[0]*1000, color=colors[3], linestyle='--'))

labels = ["Config 1", "Config 2", "Config 3"]


# Polish    
axs[1].set_xticklabels(labels, rotation=0,fontsize=labelsize)
axs[1].set_xlabel("Threshold-Config", fontsize=labelsize)
axs[0].set_xticks([])
axs[0].set_xlabel("")
axs[0].set_title("(a) Simulation results", fontsize=titlesize)

axs[0].tick_params(axis='both', which='major', pad=2, labelsize=labelsize)
axs[1].tick_params(axis='both', which='major', pad=2, labelsize=labelsize)
fig.align_ylabels(axs)
axs[0].set_xlim([-0.3, 2.3])
axs[1].set_xlim([-0.3, 2.3])

# Add legend   
h, l = axs[0].get_legend_handles_labels()
#legend_labels = ['13klux', '$E_{H,max@13klux}$','15klux', '$E_{H,max@15klux}$', '18klux', '$E_{H,max@18klux}$', '20klux', '$E_{H,max@20klux}$']
legend_labels = ['13klux', '15klux', '18klux', '20klux']

axs[1].legend(lines_handles, ['$E_{H,max@20klux}$'], fontsize=labelsize, labelspacing=0.0, columnspacing=0.3, handletextpad=0.1, frameon=False,borderpad=0)
if PLOT_EXPERIMENTAL_DATAPOINTS:
    axs[0].legend(handles=[mlines.Line2D([], [], color='black', marker='x', linestyle='None', label='Measured values')], fontsize=labelsize, handletextpad=0.2)

handles = h
fig.legend(handles,legend_labels, ncol=4, loc='lower center', fontsize=labelsize, labelspacing=0.0, columnspacing=0.3, handletextpad=0.1, handlelength=2)
fig.subplots_adjust(top=0.893,
bottom=0.255,
left=0.174,
right=0.973,
hspace=0.157,
wspace=0.285)
fig.savefig("BotoksThresholdsAM1417.pdf")

#%% Plot IV curves for both solar panels and with corresponding voltage range
v_low = 2.4
v_high = [2.65, 3.05, 3.65]

fig, ax = plt.subplots(figsize=(3, 2.7))

for lux, c, p_label in zip([15000, 20000], [colors[1], colors[3]], ['$P_{MPP@15klux}$', '$P_{MPP@20klux}$']):
    harvest_config_solar['settings']['file'] = f'{panel}_lux{lux}.json'
    harvester = harvester_factory(harvest_config_solar, sim.min_step_size)
    harvester.reset(0)
    iv_curve = harvester.iv_curve.copy()
    iv_curve['current'] = iv_curve.current * 1e3
    #iv_curve.plot(x='voltage', y = 'current' ,ax=ax)
    power = iv_curve.voltage * iv_curve.current

    #Polish a bit because of the way we recorded the IV cirve
    from scipy.interpolate import make_interp_spline
    import numpy as np
    xnew = np.linspace(iv_curve.voltage.min(), iv_curve.voltage.max(), 100)  
    spl = make_interp_spline(iv_curve.voltage[0:-8].append(iv_curve.voltage[-1:]), power[0:-8].append(power[-1:]), k=2)
    power_smooth = spl(xnew)#spline(iv_curve.voltage, power, xnew)
    
    ax.plot(xnew, power_smooth, label=f"{int(lux/1000)}klux", color=c)
    ax.axhline(y=power.max(), label = p_label, linestyle='--', alpha = 0.5, color=c)


label_start = 1.35
label_height = 0.1
top = label_start + 2* label_height + 0.1
      
for v_h, C_label, height in zip(v_high, ['Config 3', 'Config 2', 'Config 1'], [label_start, label_start + label_height, label_start + 2*label_height]):
    ax.axvline(x=v_h, color='grey')
    ax.annotate("", xy=(v_low, height), xytext=(v_h, height), xycoords='data', textcoords='data',
                horizontalalignment = 'center', arrowprops=dict(arrowstyle="<->", shrinkA = 0, shrinkB = 0,  color='grey'))
    ax.annotate(C_label, xy=(v_low - 0.05, height),  xycoords='data', textcoords='data', fontsize=labelsize, va='center',
                horizontalalignment = 'right', color='grey', alpha=1)
ax.axvline(x=v_low, color='grey')

ax.annotate('$V_{High3}$    ', xy=(v_high[0], top), xycoords='data', annotation_clip=False, ha='center',va='bottom',color='grey',fontsize=labelsize)
ax.annotate('$V_{High2}$', xy=(v_high[1], top), xycoords='data', annotation_clip=False, ha='center',va='bottom',color='grey',fontsize=labelsize)
ax.annotate('$V_{High1}$', xy=(v_high[2], top), xycoords='data', annotation_clip=False, ha='center',va='bottom',color='grey',fontsize=labelsize)
ax.annotate('$V_{Low}$', xy=(v_low, 0), xycoords='data', annotation_clip=False,  ha='right',va='bottom',color='grey',fontsize=labelsize)

#ax.set_title("(b) PV curve", fontsize=titlesize)
ax.set_ylim([0, top])
h, l = ax.get_legend_handles_labels()
fig.legend(h, l , ncol=4, loc='lower left',fontsize=labelsize, labelspacing=0.0, columnspacing=0.3, handletextpad=0.1, handlelength=1)

ax.set_ylabel("$P_H (mW)$", fontsize=labelsize,labelpad=0)
ax.set_xlabel("$V_H (V)$", fontsize=labelsize,labelpad=0)
ax.set_title("(b) PV curve", fontsize=titlesize,  pad=16)
ax.tick_params(axis='both', which='major', pad=2, labelsize=labelsize)

fig.subplots_adjust(top=0.855,
bottom=0.265,
left=0.16,
right=0.96,
hspace=0.2,
wspace=0.2)
fig.savefig("BotoksPVCurveAM1417.pdf")

#%%
stats_solar['harvesting_eff'] = stats_solar.energy_harvested_mj / (stats_solar.max_energy_harvested * 1000)
print(stats_solar[['harvesting_eff', 'v_high', 'lux']])

