# -*- coding: utf-8 -*-
"""
Showcase that the Gameboy model reflects the real behavior of the device.
Plots voltage and GPIO traces over time of data
- obtained experimentally
- obtained from Simba simulator
"""

from Simba import Simulation
import matplotlib.pyplot as plt

# Configuration(s) for simulation
from Gameboy import harvest_config_solar, capacitor_config, converter_config, load_config, cap_values, v_high_values
import gameboy_data_manager as gameboy_dh

#%%%
SIM_TIME = 10 #in seconds

v_initial = 3.38
vhigh=4.0
lux = 13000
capacitance = 3300

labelsize=9
titlesize=9

#%% Plot trace of measured data
try:
    measurement_path = "../../Artifacts/Gameboy/ExtractedData/SolarConst"
    measurement_filename = f"result_lux{lux}_vhigh{vhigh}_cap{capacitance}"
    
    ## Load trace and plot
    data_dig = gameboy_dh.load_gameboy_trace_digital(measurement_path + '/digital', measurement_filename, time_max = SIM_TIME + 1)
    data_ana = gameboy_dh.load_gameboy_trace_analog(measurement_path + '/analog', measurement_filename, time_max = SIM_TIME + 1)
    
    data_ana_orig = data_ana.copy()
    #data_ana = data_ana.iloc[::100, :] #resample for faster plotting (if orignial files are used)
    
    fig_meas, axs_meas = plt.subplots(nrows=2, sharex=True, gridspec_kw={'height_ratios': [1, 2]}, figsize=(6,1.5))
    gameboy_dh.plot_gameboy_trace(data_dig, data_ana, axs=axs_meas)
        
    # Polish
    axs_meas[1].set_xlim([0,SIM_TIME])
    axs_meas[1].legend(fancybox=True, framealpha=0, columnspacing=0, fontsize=labelsize, labelspacing=0.1, handletextpad=0.1, loc = 'center left') #legend box transparent
    
    fig_meas.suptitle("(a) Trace measured on real hardware.", fontsize=titlesize)
    axs_meas[1].set_xlim([0,SIM_TIME])
    axs_meas[1].set_xlabel("Time (s)", labelpad =-2, fontsize=labelsize)  
    axs_meas[0].tick_params(axis='both', which='major', pad=1, labelsize=labelsize)
    axs_meas[1].tick_params(axis='both', which='major', pad=1, labelsize=labelsize)
    fig_meas.subplots_adjust(top=0.9, bottom=0.2, left=0.125, right=0.985, hspace=0.29, wspace=0.215)    
    
    fig_meas.savefig("GameboyTraceMeas.pdf")#, transparent=True)
except FileNotFoundError:
    print(f"Could not find measurement data for this configuration ({measurement_filename}.pkl not found) -- skip plotting.")

#%% Plot trace of simulated data

capacitor_config['settings']['capacitance'] = cap_values[capacitance] if capacitance in cap_values else capacitance
capacitor_config['settings']['v_initial'] = v_initial

converter_config['settings']['vout_ok_high'] = v_high_values[vhigh] if vhigh in v_high_values else vhigh

load_config['settings']['v_checkpoint'] = 3.4 
load_config['settings']['verbose_log'] = True

harvest_config_solar['settings']['file'] = f'Gameboy_lux{lux}.json'
harvest_config_solar['settings']['log'] = True


sim = Simulation(capacitor_config, harvest_config_solar, converter_config, load_config)

sim.max_step_size = 2e-3
sim.run(until = SIM_TIME) 

load_log = sim.load.get_log()
harvest_log = sim.harvester.get_log()

#Plot capacitor voltage and harvesting/load currents over time
fig_sim, axs_sim = plt.subplots(nrows=2, sharex=True, gridspec_kw={'height_ratios': [1, 2]}, figsize=(6,1.5))
load_log.plot(x='time', y='v_cap', ax=axs_sim[1], color='black', label = '$V_{cap}$', linestyle='dashed')
load_log.plot(x='time', y='v_out', ax=axs_sim[1], color='grey', label = '$V_{L}$', linestyle='solid',drawstyle='steps-post')
harvest_log.plot(x='time', y='v_in', ax=axs_sim[1], color='lightgrey', label = '$V_{H}$', linestyle='dotted')
axs_sim[1].set_ylabel("Voltage (V)")#, rotation='horizontal', ha='center', va='center', labelpad=20)    
axs_sim[1].legend(fancybox=True, framealpha=0, labelspacing=0.0, handletextpad=0.2, loc = 'center left') #legend box transparent
  
#Plot incoming and outgoing currents over time
#load_log['i_out_ma'] = load_log.i_out * 1000
#harvest_log['i_in_ma'] = harvest_log.i_in * 1000
#harvest_log.plot(x='time', y='i_in_ma', ax=axs_sim[2], color='black', label = '$I_H$', drawstyle='steps-post')
#load_log.plot(x='time', y='i_out_ma', ax=axs_sim[2], color='grey', label = '$I_L$', drawstyle='steps-post')
#axs_sim[2].set_ylabel("Current\n(mA)")#, rotation='horizontal', ha='center', va='center')   
axs_sim[1].legend(fancybox=True, framealpha=0, columnspacing=0, fontsize=labelsize, labelspacing=0.1, handletextpad=0.1, loc = 'center left') #legend box transparent

#Plot states of loads in seperate plot
for state in load_log.state.unique():
    load_log[state] = (load_log.state == state).astype(int)
load_log['RESTORE'] = load_log['RESTORE']*0.8 + 2
load_log['COMPUTE'] = load_log['COMPUTE']*0.8 + 0
load_log['CHECKPOINT'] = load_log['CHECKPOINT']*0.8 + 1

load_log.plot(x='time', y=['RESTORE', 'CHECKPOINT', 'COMPUTE'], ax=axs_sim[0], drawstyle='steps-post', legend=False)
axs_sim[0].set_yticks([0, 1, 2])
axs_sim[0].set_yticklabels(['COMPUTE', 'CHKPT', 'RESTORE'], fontsize=9)

# Polish
axs_sim[0].set_title("(b) Trace obtained from $Simba$.", fontsize=titlesize, pad=1)
axs_sim[1].set_xlim([0,SIM_TIME])
axs_sim[1].set_xlabel("Time (s)", labelpad =-2, fontsize=labelsize)  
axs_sim[0].tick_params(axis='both', which='major', pad=1, labelsize=labelsize)
axs_sim[1].tick_params(axis='both', which='major', pad=1, labelsize=labelsize)

fig_sim.subplots_adjust(top=0.9, bottom=0.2, left=0.125, right=0.985, hspace=0.29, wspace=0.215)    
fig_sim.savefig("GameboyTraceSim.pdf")#, transparent=True)

