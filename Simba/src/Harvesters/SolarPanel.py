# -*- coding: utf-8 -*-
"""
Harvester module implementation:

Solar panel

The `SolarPanel` module allows to use long-term real-world solar energy harvesting traces in simulation, by including
- a [PV cell model](https://www.mdpi.com/1996-1073/9/5/326) that can be configured according to parameters that are typically available in datasheets, and
- real-world solar irradiance traces from existing datasets (e.g., [NREL](https://midcdmz.nrel.gov/apps/sitehome.pl?site=BMS) for outdoor and [ENHANTS](https://enhants.ee.columbia.edu/indoor-irradiance-meas) for indoor environments).
"""

import pandas as pd
import numpy as np
import json
import matplotlib.pyplot as plt
import os
import inspect
                    
class SolarPanel:
     
    def __init__(self, config, verbose, time_base):
        self.verbose = verbose
        if verbose:
            print("Create Solar Panel Source.")
        
        self.time_base = time_base
        self.log_full = config['log'] if 'log' in config else False
        self.next_update = 0
        
        self.t_start = config['t_start'] if 't_start' in config else None
        self.t_max = config['t_max'] if 't_max' in config else None
        self.file = config['file']
        
        #Configure panel related data from datasheet (I_sc, V_oc etc.)
        self.i_sc = config['i_sc']
        self.v_oc_nom = config['v_oc']
        self.i_mpp = config['i_mpp']
        self.v_mpp = config['v_mpp']
        if 'num_cells' in config and config['num_cells'] > 1:
            #if connected in series, currents values change -- else voltages 
            if config['connection'] == 'series':
                self.v_oc_nom *= config['num_cells']
                self.v_mpp *= config['num_cells']
            else:    
                self.i_sc *= config['num_cells']
                self.i_mpp *= config['num_cells']
             
        #compute look-up-table for delivered current depending on input voltage
        #(See: A Complete and Simplified Datasheet-Based Model of PV Cells in Variable Environmental Conditions for Circuit Simulation)
        self.v_factor = np.array([self.i_sc * (1 - np.exp(np.log(1 - self.i_mpp/self.i_sc) * (voltage - self.v_oc_nom) / (self.v_mpp - self.v_oc_nom))) for voltage in np.arange(0, self.v_oc_nom, 0.01)])
                    

    def reset(self, initial_voltage):
        
        self.load_irradiance_data()
        self.current_irradiance = self.irradiance[1][0]
        #(See: Effect of Illumination Intensity on Solar Cells Parameters)
        #Using formula 12 and added a scaling factor depending on v_oc at standard test condition of 1000 irradiation
        #self.v_oc = self.v_oc_nom + 0.02569 * np.log(self.current_irradiance / 1000.0) * self.v_oc_nom / 0.616
        self.v_oc = self.v_oc_nom 
        self.log = [{'time' : 0, 
                    'i_in' : self.get_current(0, initial_voltage), 
                    'v_in' : initial_voltage, 
                    'i_max' : self.get_current(0, self.v_mpp),
                    'irr' :  self.current_irradiance}]
        self.log_processed = False
        self.stats = {'energy_total' : 0, 'energy_max' : 0}
        
    def update_state(self, time, dt, voltage):
        i_new = self.get_current(time, voltage)
        i_max_new = self.get_current(time, self.v_mpp * self.v_oc/self.v_oc_nom)
        if self.log_full:
            if i_new != self.log[-1]['i_in'] or i_max_new != self.log[-1]['i_max']:
                self.log.append({'time' : time * self.time_base, 
                                 'i_in' : i_new,
                                 'v_in' : voltage,
                                 'i_max' : i_max_new,
                                 'irr' :  self.current_irradiance})
        self.stats['energy_total'] += i_new * voltage * dt * self.time_base
        self.stats['energy_max']   += i_max_new * self.v_mpp * self.v_oc/self.v_oc_nom * dt * self.time_base
                    
            
    def process_log(self, time_max):
        if self.log_full:
            self.log = pd.DataFrame(self.log)
            self.log.loc[:,'dt'] = abs(self.log.time.diff(-1))
            self.log.loc[self.log.index[-1], 'dt'] = time_max - self.log.time.iloc[-1]
            self.log['p_in'] = self.log.i_in * (self.log.v_in.shift(-1) + self.log.v_in)/2 #interpolate/estimate power consumption between two different voltage points
            self.log['p_max'] = self.log.i_max *  self.v_mpp
        self.log_processed = True
            
    def get_log(self):
        if not self.log_processed:
            self.process_log()
        
        return self.log
    
    def get_log_stats(self, normalize):
        
        self.stats['i_in_max'] = self.log.i_in.max()
        self.stats['i_in_mean'] = self.log.i_in.mean()
        self.stats['p_in_max'] = self.log.p_in.max()
        self.stats['p_in_mean'] = self.log.p_in.mean()
        self.stats['irr_min'] = self.irradiance[1].min()
        self.stats['irr_mean'] = self.irradiance[1].mean()
        return self.stats
               
    def get_ocv(self, time):        
        # we look up the irradiance only if it has changed to improve simulation speed
        # store next update time in self.next_update
        #if time >= self.next_update:
        #     idx = np.argwhere(self.irradiance[0] >= time)[0][0]
        #     self.current_irradiance = self.irradiance[1][idx]
        #     if idx < len(self.irradiance[0]) - 1:
        #         self.next_update = self.irradiance[0][idx + 1]
        #     else:
        #         self.next_update = self.time_max
        
        #     #(See: Effect of Illumination Intensity on Solar Cells Parameters)
        #     #Using formula 12 and added a scaling factor depending on v_oc at standard test condition of 1000 irradiation
        #     if self.current_irradiance > 1:
        #        # k = 1.380649e-23
        #         self.v_oc = self.v_oc_nom + 0.02569 * np.log(self.current_irradiance / 1000.0) * self.v_oc_nom / 0.616
        #     else:
        #         self.v_oc = 0
        self.v_oc = self.v_oc_nom
        return self.v_oc_nom
    
    def get_current(self, time, voltage = 0):
                
        if time >= self.next_update:
            idx = np.argwhere(self.irradiance[0] >= time)[0][0]
            self.current_irradiance = self.irradiance[1][idx]
            self.current_current = self.current_irradiance / 1000.0 * self.v_factor[int((voltage/self.v_oc_nom) * len(self.v_factor))]
            if idx < len(self.irradiance[0]) - 1:
                self.next_update = int(self.irradiance[0][idx + 1])
            else:
                self.next_update = int(self.time_max)
        
        #we compute the current dep. on irradiance 
        #(See: A Complete and Simplified Datasheet-Based Model of PV Cells in Variable Environmental Conditions for Circuit Simulation)
        if voltage >= self.v_oc_nom:  #panel cannot deliver anymore
            return 0
        return self.current_current
            
    def get_next_change(self, time):
        if time >= self.time_max:
            return None
        return self.next_update - time
            
    def load_irradiance_data(self):
            
            file_path = os.path.join(os.path.dirname(inspect.getfile(self.__class__)),f"harvesting_data/SolarTraces/{self.file}")          
        
            with open(file_path, 'r') as file:
                info = json.loads(file.readline())
                df = pd.read_json(file)
                if self.verbose:
                    print(f"Successfully loaded irradiance data from {self.file}.")
                  
            if self.t_start != None:
                assert info['TraceLength'] >= self.t_start , "ERROR: Starting time of solar source exceeds trace length." 
                df = df[df.index >= self.t_start].copy()
                df.index = df.index - df.index[0] #er start at t=0
            
            if self.t_max != None:
                assert df.index.max() >= self.t_max, "ERROR: Simulation time of solar source exceeds trace length."
                df = df[df.index <= self.t_max].copy() #crop
              
            # Convert time to integer according to time base from simulation   
            df.index = (df.index / self.time_base)
            
            self.irradiance = np.array([df.index, df.irradiance]) #convert to np array for faster simulation speeds
            self.time_max = int(self.irradiance[0].max()) #0 .. time, 1 ... irradiance
            
            
    def plot_irradiance_trace(self, axs = []):
        self.reset(0)
        if len(axs) == 0:
            fig, axs = plt.subplots(3)
        
        axs[0].step([x * self.time_base for x in self.irradiance[0]], self.irradiance[1], where='pre', label='irradiance')
        axs[1].step([x * self.time_base for x in self.irradiance[0]], [x * 122 for x in self.irradiance[1]], where='pre', label='lux')
        counts, bins = np.histogram([x * 122 for x in self.irradiance[1]], bins=100)
        axs[2].stairs(counts, bins)
        axs[0].set_ylabel("Irradiance (W/m)")
        axs[1].set_ylabel("Illuminance (lux)")
        axs[0].set_xlabel("Time (s)")
        axs[1].set_xlabel("Time (s)")
       