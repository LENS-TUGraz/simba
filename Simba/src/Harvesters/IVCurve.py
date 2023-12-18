# -*- coding: utf-8 -*-
"""
Harvester module implementation:

IV Curve

The `IVCurve` module contains the IV curve of a energy harvester at the certain environmental condition 
(e.g., for solar panel this means a single IV-curve at a certain brightness). 
This module thus allows to incorporate the non-linear behavior of many harvesters into the simulation. 

The IV-curves are stored in *Harvesters/harvesting_data/IVCurves* as `.json`-Files. To add new IV-Curves, 
see *Tools/get_iv_curve_XXXX.py* and the corresponding Readme.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import math
import inspect
import os

class IVCurve:
    
    def __init__(self, config, verbose, time_base):
        self.verbose = verbose
        if verbose:
            print("Create IV Curve Source.")
        self.time_base = time_base
        self.next_update = 0
        #TODO: make loading of iv curve properly!
        self.iv_file = config['file']
        self.lux = config['lux'] if 'lux' in config else 0
        self.log_full = config['log'] if 'log' in config else True
        self.time_max = math.inf
            
    def reset(self, initial_voltage):
        
        #TODO: remove this ugly hack and make loading dep. on lux properly
        self.load_iv_curve()
        
        self.log = [{'time' : 0, 
                     'i_in' : self.get_current(0, initial_voltage), 
                     'v_in' : initial_voltage, 
                     'p_max' : self.get_max_power()}]
        self.log_processed = False
        self.stats = {'energy_total' : 0,
                      'energy_max' : 0}
        
    def update_state(self, time, dt, voltage):
        
        i_new = self.get_current(time, voltage)
        if self.log_full:
            if i_new != self.log[-1]['i_in'] or abs(time - self.log[-1]['time']) > 0.5:
                self.log.append({'time' : time * self.time_base, 
                                 'i_in' : i_new,
                                 'v_in' : voltage,
                                 'p_max' : self.get_max_power()})
                
        self.stats['energy_total'] += i_new * voltage * dt * self.time_base
        self.stats['energy_max'] += self.get_max_power() * dt * self.time_base
            
            
    def process_log(self, time_max):
        if self.log_full:
            self.log = pd.DataFrame(self.log)
            self.log.loc[:,'dt'] = abs(self.log.time.diff(-1))
            self.log.loc[self.log.index[-1], 'dt'] = time_max * self.time_base - self.log.time.iloc[-1]
            self.log['p_in'] = self.log.i_in * (self.log.v_in.shift(-1) + self.log.v_in)/2 #interpolate/estimate power consumption between two different voltage points
        self.log_processed = True
            
    def get_log(self):
        if not self.log_processed:
            self.process_log()
        
        return self.log
    
    def get_log_stats(self, normalize):
        return self.stats
    
    def get_ocv(self, time):
        if hasattr(self, 'iv_curve'):
            return self.iv_curve.voltage.max() 
        else:
            self.load_iv_curve()
            return self.iv_curve.voltage.max()
               
    def get_current(self, time, voltage = 0):
        
        # Interpolate between closest points on IV curve
        self.current = np.interp(voltage, self.iv_curve['voltage'], self.iv_curve['current'])
            
        return self.current 
        
    def get_max_power(self):
        return self.max_power
        
    def get_next_change(self, time):
        return None
            
    def load_iv_curve(self):
        
        if 'XXXXX' in self.iv_file:
            file = self.iv_file.replace('XXXXX', str(self.lux)) #TODO: make properly
        else:
            file = self.iv_file
        
        file_path = os.path.join(os.path.dirname(inspect.getfile(self.__class__)),f"harvesting_data/IVCurves/{file}")          
        df = pd.read_json(file_path, convert_axes=False)
        df = df.reset_index().astype(float)
        df = df.rename({"index" : "voltage", "0" : "current"}, axis=1)
        df['current'] = abs(df.current)
        if self.verbose:
            print(f"Successfully loaded IV curve from {file}.")
                  
        self.iv_curve = df # TODO: convert to numpy array for faster simulation speed
        self.max_power = (df.current * df.voltage).max()
        
    def plot_iv_curve(self, ax=None):
        if ax == None:
            fig, ax = plt.subplots()
        self.iv_curve.plot(x='voltage', y = 'current' ,ax=ax)
        power = self.iv_curve.voltage * self.iv_curve.current
        ax.plot(self.iv_curve.voltage, power, label = 'power')
        ax.set_ylabel("I (A)")
        ax.set_xlabel("V (V)")
                  
 