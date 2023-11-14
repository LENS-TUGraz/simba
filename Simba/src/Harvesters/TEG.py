# -*- coding: utf-8 -*-
"""
Harvester module implementation:

TEG data set

TODO: description
"""

import pandas as pd
import numpy as np
import json
import matplotlib.pyplot as plt
import math
      
class TEG:
     
    def __init__(self, config, verbose, time_base):
        self.verbose = verbose
        if verbose:
            print("Create TEG Source.")
        self.time_base = time_base
            
        self.log_full = config['log'] if 'log' in config else True
        self.data_type = config['data_type']
        self.next_update = 0
        
        if self.data_type == 'Impp':
            self.load_impp_data(config)
            
        elif self.data_type == 'Raw':
            assert False, "Raw TEG data not implemented yet."
            
    def reset(self, initial_voltage):
        self.log = [{'time' : 0, 
                     'i_in' : self.get_current(0, initial_voltage), 
                     'v_in' : initial_voltage}]
        self.log_processed = False
        self.stats = {'energy_total' : 0}
        
    def update_state(self, time, dt, voltage):
        i_new = self.get_current(time, voltage)
        if self.log_full:
            if i_new != self.log[-1]['i_in']:
                self.log.append({'time' : time * self.time_base, 
                                 'i_in' : i_new,
                                 'v_in' : voltage})
        self.stats['energy_total'] += i_new * voltage * time * self.time_base
                
            
    def process_log(self, time_max):
        if self.log_full:
            self.log = pd.DataFrame(self.log)
            self.log.loc[:,'dt'] = abs(self.log.time.diff(-1))
            self.log.loc[self.log.index[-1], 'dt'] = time_max * self.time_base - self.log.time.iloc[-1]
            self.log['p_in'] = self.log.i_in * self.log.i_in * (self.log.v_in.shift(-1) + self.log.v_in)/2 #interpolate/estimate power consumption between two different voltage points
            self.log_processed = True
            
    def get_log(self):
        if not self.log_processed:
            self.process_log(0)
        
        return self.log
    
    def get_log_stats(self, normalize):
        return self.stats
    
    def get_ocv(self, time): #
        return None ##should not be used with converters that need an open circuit voltage
               
    def get_current(self, time, voltage = 0):
        assert time < self.time_max
        
        # we look up the next current value only if it has changed to improve simulation speed
        # store next update time in self.next_update
        if time >= self.next_update:
            idx = np.argwhere(self.i_trace[0] >= time)[0][0]
            self.current = self.i_trace[1][idx]
            if idx < len(self.i_trace[0]) - 1:
                self.next_update = int(self.i_trace[0][idx + 1])
            else:
                self.next_update = int(self.time_max)
        
        return self.current
            
    def get_next_change(self, time):
        if time >= self.time_max:
            return None
        return self.next_update - time
            
    def load_impp_data(self, config):
            df = pd.read_hdf(config['file'])
            if self.verbose:
                print(f"Successfully loaded TEG data from {config['file']}.")
            
            df['time'] = (df.index - df.index[0]).total_seconds()
            df['time'] = round(df.time, 1)
            trace_length = df.time.max()
            df['boost_ichg_ua'] = df.boost_ichg_ua * 1e-6 #convert to A from uA
            df = df[['time', 'boost_ichg_ua']].set_index('time')
                  
            if 't_start' in config:
                assert trace_length >= config['t_start'], "ERROR: Starting time of TEG source exceeds trace length." 
                df = df[df.index >= config['t_start']].copy()
            
            if 't_max' in config: 
                assert trace_length >= config['t_max'], "ERROR: Simulation time of solar source exceeds trace length."
                df = df[df.index <= config['t_max']].copy() #crop
              
            df.index = (df.index / self.time_base)
            
            self.i_trace = np.array([df.index, df.boost_ichg_ua]) #convert to np array for faster speeds
            self.time_max = int(self.i_trace[0].max()) #0 .. time, 1 ... irradiance
            
            
    def plot_data(self, ax = None):
        if ax == None:
            fig, ax = plt.subplots()
        ax.step([t * self.time_base for t in self.i_trace[0]], self.i_trace[1], where='pre')
        ax.set_ylabel("Generated TEG current (A)")
        ax.set_xlabel("Time (s)")
            
            