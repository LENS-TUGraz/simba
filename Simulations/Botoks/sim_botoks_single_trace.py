# -*- coding: utf-8 -*-
"""
Showcase that the Botoks model reflects the real behavior of the device.
Plots voltage and GPIO traces over time of data
- obtained experimentally
- obtained from Simba simulator
"""

#%%

from Simba import Simulation
import matplotlib.pyplot as plt
import botoks_data_handler as botoks_dh

# Import Botoks module onfigurations for simulation
from Botoks import harvest_config, capacitor_config, converter_config, load_config_burn, cap_values

## Select which configuration to plot
SIM_TIME = 0.4 #in seconds
current = 600
capacitance = 100

labelsize=9
titlesize=9

#%% Plot trace of measured data

## Load trace of measurement with logic analyzer
measurement_path = "../../Artifacts/Botoks/ExtractedData/DataCapsizesJson"
measurement_filename = f"result_burn_cap{capacitance}_{current}"

try:
    data_dig = botoks_dh.load_botoks_trace_digital(measurement_path + '/digital', measurement_filename, time_max = SIM_TIME + 1)
    data_ana = botoks_dh.load_botoks_trace_analog(measurement_path + '/analog', measurement_filename, time_max = SIM_TIME + 1)

    ## Cut beginning to synchronze starting point of plots (at certain voltage level)
    start_t = data_ana[abs(data_ana.V_CAP - 2.4) < 0.01].Time.iloc[0]
    data_dig = data_dig[data_dig.Time > start_t]
    data_dig.Time = data_dig.Time - data_dig.Time.iloc[0]
    data_ana = data_ana[data_ana.Time > start_t]
    data_ana.Time = data_ana.Time - data_ana.Time.iloc[0]
    
    ## Plot and polish
    fig_meas, axs_meas = plt.subplots(nrows=2, sharex=True, gridspec_kw={'height_ratios': [1, 2.0]}, figsize=(6,1.5))
    botoks_dh.plot_botoks_trace(data_dig, data_ana, axs=axs_meas)
    
    axs_meas[1].set_xlim([0,SIM_TIME])
    axs_meas[1].legend(fancybox=True, framealpha=0, labelspacing=0.1, columnspacing =0.1, handletextpad=0.1, loc = 'center left',fontsize=labelsize, ) #legend box transparent
      
    fig_meas.suptitle("(a) Trace measured on real hardware.", fontsize=titlesize)   
    
    axs_meas[1].set_xlabel("Time (s)", labelpad =-2, fontsize=labelsize)  
    axs_meas[0].tick_params(axis='both', which='major', pad=1, labelsize=labelsize)
    axs_meas[1].tick_params(axis='both', which='major', pad=1, labelsize=labelsize)
    
    fig_meas.subplots_adjust(top=0.9, bottom=0.2, left=0.115, right=0.975, hspace=0.29, wspace=0.215)    
    fig_meas.savefig("BotoksTraceMeas.pdf")#, transparent=True)
    
except FileNotFoundError:
    print(f"Could not find measurement data for this configuration ({measurement_filename}.pkl not found) -- skip plotting.")

#%% Plot trace of simulated data  

capacitor_config['settings']['capacitance'] = cap_values[int(capacitance)]
capacitor_config['settings']['v_initial'] = 2.395
harvest_config['settings']['i_high'] = current * 1e-6 
load_config_burn['settings']['verbose_log'] = True  #we wan't as many datapoints as possible to have a smooth plot

# Create simulator environments and run simulation
sim = Simulation(capacitor_config, harvest_config, converter_config, load_config_burn)
sim.max_step_size = 1e-3
sim.run(until = SIM_TIME) 

# Retrieve logging data
load_log = sim.load.get_log()
harvest_log = sim.harvester.get_log()

#Plot capacitor voltage and harvesting/load currents over time
fig_sim, axs_sim = plt.subplots(nrows=2, sharex=True, gridspec_kw={'height_ratios': [1, 2.0]}, figsize=(6,1.5))
load_log.plot(x='time', y='v_cap', ax=axs_sim[1], color='black', label = '$V_{cap}, V_H$', linestyle='dashed')
load_log.plot(x='time', y='v_out', ax=axs_sim[1], color='grey', label = '$V_{L}$', linestyle='solid')
axs_sim[1].set_ylabel("Voltage (V)")#, rotation='horizontal', ha='center', va='center', labelpad=20)    
axs_sim[1].legend(fancybox=True, framealpha=0, labelspacing=0.1, columnspacing =0.1, handletextpad=0.1, loc = 'center left',fontsize=labelsize, ) #legend box transparent
  
#Plot incoming and outgoing currents over time
#load_log['i_out_ma'] = load_log.i_out * 1000
#harvest_log['i_in_ma'] = harvest_log.i_in * 1000
#harvest_log.plot(x='time', y='i_in_ma', ax=axs_sim[2], color='black', label = '$I_H$', drawstyle='steps-post')
#load_log.plot(x='time', y='i_out_ma', ax=axs_sim[2], color='grey', label = '$I_L$', drawstyle='steps-post')
#axs_sim[2].set_ylabel("Current\n(mA)")#, rotation='horizontal', ha='center', va='center')   
#axs_sim[1].legend(fancybox=True, framealpha=0, labelspacing=0.2, columnspacing=0,  fontsize=labelsize, handletextpad=0.2, loc = 'center left') #legend box transparent

#Plot states of loads in seperate plot
for state in load_log.state.unique():
    load_log[state] = (load_log.state == state).astype(int)

#each line is one GPIO trace
load_log['SENSE'] = load_log['SENSE']*0.8 + 0
load_log['SEND'] = load_log['SEND']*0.8 + 1
load_log['BURN'] = load_log['BURN']*0.8 + 2

load_log.plot(x='time', y=['SENSE', 'SEND', 'BURN'], ax=axs_sim[0], drawstyle='steps-post', legend=False)
axs_sim[0].set_yticks([0, 1, 2])
axs_sim[0].set_yticklabels(['SENSE', 'SEND', 'BURN'], fontsize=9)
                           
# Polish
axs_sim[1].set_xlim([0,SIM_TIME])
axs_sim[1].set_xlabel("Time (s)", labelpad =-2, fontsize=labelsize)  
axs_sim[0].tick_params(axis='both', which='major', pad=1, labelsize=labelsize)
axs_sim[1].tick_params(axis='both', which='major', pad=1, labelsize=labelsize)

axs_sim[0].set_title("(b) Trace obtained from $Simba$.", fontsize=titlesize, pad=1)
fig_sim.subplots_adjust(top=0.9, bottom=0.2, left=0.115, right=0.975, hspace=0.29, wspace=0.215)    
fig_sim.savefig("BotoksTraceSim.pdf")#, transparent=True)