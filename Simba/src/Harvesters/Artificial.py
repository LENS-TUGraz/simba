# -*- coding: utf-8 -*-
"""
Harvester module implementation:

Artificial source

The `Artificial` energy source can supply current either constantly or as a sine/square wave 
(more waveforms can be implemented on demand) with adjustable current amplitude and duty cycle.
"""

import pandas as pd
import numpy as np
import math
            
class Artificial:
    
    def __init__(self, config, verbose, time_base):
        self.verbose = verbose
        if verbose:
            print("Create Artificial Source.")
        self.time_base = time_base               
        self.shape = config['shape']
        self.time_max = math.inf
        self.v_oc = config['v_oc'] if 'v_oc' in config else 5
        self.v_ov = config['v_ov'] if 'v_ov' in config else 5
        self.log_full = config['log'] if 'log' in config else False
        
        if config['shape'] == 'const':
            self.i_high = config['i_high']
            
        elif config['shape'] == 'square':
            self.t_high = config['t_high']
            self.t_low = config['t_low']
            self.i_high = config['i_high']
            self.i_low = config['i_low']
            self.period = self.t_high + self.t_low
            
        elif config['shape'] == 'sine':
            self.period = config['period']
            self.i_high = config['i_high']
            
    def reset(self, initial_voltage):
        
        if self.shape == 'square':
            self.t_high_s = int(self.t_high / self.time_base)
            self.t_low_s = int(self.t_low / self.time_base)
            self.period_s = int(self.period / self.time_base)
        elif self.shape == 'sine':
            self.period_s = int(self.period / self.time_base)
            
        self.log = [{'time' : 0, 
                     'i_in' : self.get_current(0, initial_voltage),
                     'v_in' : initial_voltage}]
        self.log_processed = False
        self.stats = {'energy_total' : 0}
        

    def update_state(self, time, dt, voltage):
        if self.log_full:
            self.log.append({'time' : time * self.time_base, 
                             'i_in' : self.get_current(time, voltage),
                             'v_in' : voltage})
        self.stats['energy_total'] += self.get_current(time, voltage) * voltage * dt * self.time_base      
    
    def get_ocv(self, time):
        return self.v_oc
    
    def get_current(self, time, voltage = 0):
        if voltage >= self.v_ov:
            return 0
        
        if self.shape == 'const':
            return self.i_high
        elif self.shape == 'square':
            t_cycle = time % (self.period_s)
            if t_cycle < self.t_high_s:
                return self.i_high
            else:
                return self.i_low
        else:
            t_cycle = time % self.period_s
            return self.i_high * (0.5 * (np.sin(t_cycle/self.period_s * 2*np.pi) + 1))
            
        
    def get_next_change(self, time):
        if self.shape == 'const' or self.shape == 'sine':
            return None
        elif self.shape == 'square':
            t_cycle = time % self.period_s
            if t_cycle == self.period_s: #fix for floating point problems
                return self.t_high_s
            if t_cycle < self.t_high_s:
                return self.t_high_s - t_cycle
            else:
                return self.period_s - t_cycle
            
    def process_log(self, time_max):
        if self.log_full:
            self.log = pd.DataFrame(self.log)
            self.log.loc[:,'dt'] = abs(self.log.time.diff(-1))
            self.log.loc[self.log.index[-1], 'dt'] = time_max*self.time_base - self.log.time.iloc[-1]
            self.log['p_in'] = self.log.i_in * (self.log.v_in.shift(-1) + self.log.v_in)/2 #interpolate/estimate power consumption between two different voltage points
        self.log_processed = True
            
    def get_log(self):
        if not self.log_processed:
            self.process_log(0)
        
        return self.log
    
    def get_log_stats(self, normalize):
        return self.stats
            
