# -*- coding: utf-8 -*-
"""
Simple example of simulating a JIT-checkpointing load with different capacitor sizes.
"""
#%%

from Simba import Simulation
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

# Configuration(s) for simulation

# Constant current harvesting
harvest_config_const = {
    'type' :  'Artificial',
    'settings' : {'shape' : 'const',
                  'i_high' : 400e-6}
    }

# Load with single, continuous task operating between 3.3 and 2.1 V
load_config = {
    'type' : 'AdvancedJITLoad',
    'settings' : {  'application' : {'type' : 'Computation',
                                     'i_active': 1000e-6},             
                    'currents' : {'OFF' : 26e-6,
                                  'RESTORE' : 971e-6,
                                  'SAVE' : 811e-6},
                    't_restore' : 5e-3,
                    't_save' : 5e-3,
                    'v_restore' : 3.3,
                    'v_save' : 2.1,
                    'v_min' : 1.8,
                    'initial_state' : 'ON'}
    }

# Ideal capacitor model or tantulum model (considers leakage)
capacitor_config = {
    'type' : 'IdealCapacitor',
    'settings': {'capacitance' : 50e-6,
                'v_rated' : 10,
                'v_initial' : 3.3,
                'log' : True}
    }

# Direct coupling between harvester and capacitor
converter_config = {
    'type' : 'Diode',
    'settings' : {'v_ov' : 3.3}}

# Compute simple statistics from load logs
def get_stats(df):
    df = df[df.index <= df[df.state == 'RESTORE'].index.max()].copy() #copy to avoid python warnings
    df['Interval'] = abs(df.time.diff(-1))
        
    reactivity = df[(df.state == 'OFF') & (df.dt > 0)].dt.mean()
    
    grouped_sum = df.groupby('state').Interval.sum()
    grouped_count = df.groupby('state').Interval.count()
    
    return {
        'time_total' : grouped_sum.sum(),
        'time_on' : grouped_sum.ON,
        'time_off' : grouped_sum.OFF,
        'num_saves' : grouped_count.SAVE,
        'num_restores' : grouped_count.RESTORE,
        'forward_progress' : grouped_sum.ON / grouped_sum.sum(),
        'reactivity' : reactivity}
  
SIM_TIME=10 #simulation time for each run in seconds

caps = [50e-6, 20e-6]
i_in = [500e-6, 800e-6]

color_map = {'ON' : 'green',
             'SAVE' : 'darkgrey',
             'RESTORE' : 'darkgrey',
             'OFF' : 'red'}

for i in i_in:

    fig, axs = plt.subplots(ncols=2, figsize=(5,3))
    
    for cap, ax in zip(caps, axs):
        capacitor_config['settings']['capacitance'] = cap
        harvest_config_const['settings']['i_high'] = i

        sim = Simulation(capacitor_config, harvest_config_const, converter_config, load_config)   
        df = pd.DataFrame()
        sim.run(until = SIM_TIME) 
            
        load_log = sim.load.get_log()
        harvest_log = sim.harvester.get_log()
        cap_log = sim.cap.get_log()
        
        #Plot voltage and currents over time
        cap_log.plot(x='time', y='voltage', ax=ax, color='black', legend=False)
        y0, y1 = ax.get_ylim()
        
        #Color the trace background according to load state
        for idx, row in load_log.iloc[:-1].iterrows():
             ax.fill_between([row.time, load_log.iloc[idx + 1].time], y0, y1, color = color_map[row.state], alpha=0.3)
        #Legend for state colors
        legend_elements = []
        for state in ['ON', 'OFF', 'SAVE']:# sim.log.state.unique():
            legend_elements.append(Patch(facecolor=color_map[state], edgecolor=color_map[state], label=state if state != 'SAVE' else 'SAVE/RESTORE', alpha=0.2))
        fig.legend(handles=legend_elements, loc='lower left', ncol = len(legend_elements))
        
        #Draw also tresholds.
        ax.axhline(y=load_config['settings']['v_min'], color='grey')
        ax.axhline(y=load_config['settings']['v_restore'], color='grey')

        #Polish
        ax.set_xlim([0, 0.5])
        ax.set_ylim([y0, y1])
        ax.set_ylabel("Capacitor\nVoltage (V)")
        ax.set_xlabel("Time (s)")
          
        #Get stats and plot on figure
        stats = get_stats(load_log)
        ax.set_title(f"C = {cap*1e6} uF\nForward progress = {stats['forward_progress']:.3f}\n" + "$T_{off,mean}$ = "+f"{stats['reactivity']:.3f}")
        
    fig.suptitle("$I_{in}$ = " + f"{i * 1e6} uA")  
    fig.tight_layout()
    fig.subplots_adjust(bottom=0.3)
    # bottom=0.32,
    # left=0.11,
    # right=0.97,
    # hspace=0.2,
    # wspace=0.29)
