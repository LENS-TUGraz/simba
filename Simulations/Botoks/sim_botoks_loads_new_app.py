# -*- coding: utf-8 -*-
"""
Simulate three different applications on intermittently powered Botoks platform and show energy efficiency/on times etc.
In any case, the Botoks platform should perform a simple send and sensing application (Sense and immediately send afterwards).

In the first case, the platform goes to sleep mode after transmission, remains there for x seconds and tries to sense/send afterwards.
In the second case, the platform 'burns' its remaining energy and waits until the capacitor recharges to perform the next sense/send cycle.
In the third case, the platform turns itself (i.e., the load) off after transmission to recharge as soon as possible without depleting the capacitor first. 

--> Same as sim_botoks_loads.py, but without experimental data and with longer sensing times and additional load implementation
"""

from Simba import Simulation, harvester_factory, load_factory
import pandas as pd
import matplotlib.pyplot as plt

# Import Botoks module configurations for simulation
from Botoks import harvest_config, capacitor_config, converter_config,  load_config_burn_new, load_config_loop_new, load_config_shutoff

# Specify which experiments we make
SIM_TIME = 30 #We simulate for 10 seconds (we also measured for 10 seconds)
currents = [200, 400, 600, 800, 1000]
loads = [load_config_burn_new, load_config_loop_new, load_config_shutoff]
capacitor_config['settings']['capacitance'] = 110e-6 #Original Botoks capacitance (=100uF), real, measured capacitance = 110uF


# Create simulation environment
sim = Simulation(capacitor_config, harvest_config, converter_config, load_config_loop_new)
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
        
        c_stats = pd.DataFrame(sim.load.get_log_stats(), index=[0])
        c_stats['current'] = int(current)
        c_stats['load'] = load['name']
        
        stats = pd.concat([stats, c_stats])
                    
stats = stats.reset_index(drop=True)
#%% Compute energy statistics
#Compute wasted energy depending on load type
#1) For 'burn' applications the wasted energy is either the energy in burn state (after successful sending) or everything until the burning (if sending was not successful)
stats.loc[stats.load.str.contains('Burn'), 'energy_wasted_total'] = stats.loc[stats.load.str.contains('Burn'), :].apply(lambda x : x.energy_BURN if x.energy_BURN != 0 else x.energy_INIT + x.energy_SEND + x.energy_SENSE, axis=1)
#2) For 'loop' applications, we need to sum up everything that did not lead to successful transmission
amount_useless_sensing_and_init = stats.loc[stats.load.str.contains('Loop'), 'num_fail_SEND'] / (stats.loc[stats.load.str.contains('Loop'),'num_success_SEND'] + stats.loc[stats.load.str.contains('Loop'), 'num_fail_SEND'])
amount_useless_init = stats.loc[stats.load.str.contains('Loop'),'num_fail_SENSE'] / (stats.loc[stats.load.str.contains('Loop'),'num_success_SENSE'] + stats.loc[stats.load.str.contains('Loop'),'num_fail_SENSE'])
stats.loc[stats.load.str.contains('Loop'), 'energy_wasted_total'] = stats.loc[stats.load.str.contains('Loop'), 'energy_wasted_SEND'] + stats.loc[stats.load.str.contains('Loop'), 'energy_wasted_INIT'] + stats.loc[stats.load.str.contains('Loop'), 'energy_wasted_SENSE']
stats.loc[stats.load.str.contains('Loop'), 'energy_wasted_total'] += amount_useless_sensing_and_init * (stats.loc[stats.load.str.contains('Loop'), 'energy_SENSE']  + stats.loc[stats.load.str.contains('Loop'),  'energy_INIT'])
stats.loc[stats.load.str.contains('Loop'), 'energy_wasted_total'] += amount_useless_init * stats.loc[stats.load.str.contains('Loop'), 'energy_INIT']
#3) For 'shutoff' applications, there is no energy wasted at all, only if we cannot send at least once (#todo -- failed states)

#Wasted energy in percent = total wasted energy/total energy
stats.loc[stats.load.str.contains('Burn'), 'energy_wasted_rel'] = stats.loc[stats.load.str.contains('Burn'), 'energy_wasted_total'] / (stats.loc[stats.load.str.contains('Burn'), 'energy_SENSE'] + stats.loc[stats.load.str.contains('Burn'),'energy_SEND'] + stats.loc[stats.load.str.contains('Burn'),'energy_INIT'] + stats.loc[stats.load.str.contains('Burn'),'energy_BURN'])
stats.loc[stats.load.str.contains('Loop'), 'energy_wasted_rel'] = stats.loc[stats.load.str.contains('Loop'), 'energy_wasted_total'] / (stats.loc[stats.load.str.contains('Loop'), 'energy_SENSE'] + stats.loc[stats.load.str.contains('Loop'),'energy_SEND'] + stats.loc[stats.load.str.contains('Loop'),'energy_INIT'])

#%% Normalize to 10s???
stats['num_success_SEND'] = stats['num_success_SEND'] * 10  / SIM_TIME

#%% Plot statistics of all configurations

colors = ['#377eb8', '#4daf4a', 'lightgrey']
hatches = ['//', '/', '/']
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
axs[1].set_ylabel('$T_{Sample, max}$(s)', fontsize=labelsize, labelpad=2)
axs[1].tick_params(axis='both', which='major', pad=2, labelsize=labelsize)

stats.pivot(index="current", columns="load", values="num_success_SEND").plot(kind='bar', ax=axs[2], legend=False, color=colors)
#axs[2].set_title('#Sucessful packets', fontsize=labelsize)
axs[2].set_ylabel('#Packets', fontsize=labelsize, labelpad=2)
axs[2].tick_params(axis='both', which='major', pad=2, labelsize=labelsize)

# Add legend
# h, l = axs[2].get_legend_handles_labels()
# fig.legend(h,["\'Burning\' appl.", "\'Looping\' appl."], ncol=2, loc='lower center', fontsize=labelsize)

# Polish
fig.suptitle("(b) Application with $t_{Sense} \gg t_{Send}$", fontsize=titlesize, y=0.98)
axs[2].set_xlabel("Input current $I_H$ (\u03bcA)", fontsize=labelsize, labelpad = 0)
axs[2].set_xticklabels(axs[2].get_xticklabels(), rotation=0)

h, l = axs[2].get_legend_handles_labels()
fig.legend(h,["\'BURN\'", "\'LOOP\'", "\'SHUTOFF\'"], ncol=3, loc='lower center', fontsize=labelsize)

for ax in axs:
    ax.grid(True)

fig.align_ylabels(axs)
fig.subplots_adjust(top=0.92,
bottom=0.225,
left=0.21,
right=0.96,
hspace=0.4,
wspace=0.19)

fig.savefig('BotoksLoadsNew.pdf')

#%% Print differences in percent
loop_stats = stats[stats.load.str.contains('Loop')][['current', 'load', 'time_between_SEND_max', 'num_success_SEND']].reset_index(drop=True)
burn_stats = stats[stats.load.str.contains('Burn')][['current', 'load', 'time_between_SEND_max', 'num_success_SEND']].reset_index(drop=True)
shutoff_stats = stats[stats.load.str.contains('Shut')][['current', 'load', 'time_between_SEND_max', 'num_success_SEND']].reset_index(drop=True)

#reset index, so that we can subtract each others values
loop_stats = loop_stats.reset_index(drop=True)
burn_stats = burn_stats.reset_index(drop=True)

burn_stats['DiffMaxTime'] = (burn_stats.loc[:,'time_between_SEND_max'] - loop_stats.loc[:,'time_between_SEND_max'])/burn_stats.loc[:,'time_between_SEND_max']
burn_stats['DiffNumSamples'] = (burn_stats.loc[:,'num_success_SEND'] - loop_stats.loc[:,'num_success_SEND'])/burn_stats.loc[:,'num_success_SEND']

print("Difference (%) between burning and looping application.")
print(burn_stats[['DiffMaxTime', 'DiffNumSamples']])
print("Difference (%) between shutoff and looping application.")
#shutoff_stats['DiffMaxTime'] = (shutoff_stats.loc[:,'time_between_SEND_max'] - loop_stats.loc[:,'time_between_SEND_max'])/loop_stats.loc[:,'time_between_SEND_max']
shutoff_stats['DiffMaxTime'] = (shutoff_stats.loc[:,'time_between_SEND_max'] / loop_stats.loc[:,'time_between_SEND_max'])

print(shutoff_stats[['DiffMaxTime']])
print("Difference (%) between shutoff and burning application.")
shutoff_stats['DiffMaxTime'] = (shutoff_stats.loc[:,'time_between_SEND_max'] / burn_stats.loc[:,'time_between_SEND_max'])
#shutoff_stats['DiffMaxTime'] = (shutoff_stats.loc[:,'time_between_SEND_max'] - burn_stats.loc[:,'time_between_SEND_max'])/burn_stats.loc[:,'time_between_SEND_max']
print(shutoff_stats[['DiffMaxTime']])



