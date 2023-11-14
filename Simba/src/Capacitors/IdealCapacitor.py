# -*- coding: utf-8 -*-
"""
Capacitor module implementation:

IdealCapacitor
"""

from enum import Enum
import pandas as pd

class CapacitorEvent(Enum):
    SUCCESS = 0
    OVERVOLTAGE = 1
    EMPTY = 2
    

class IdealCapacitor:   
    
    def __init__(self, config, verbose, time_base):
        self.verbose = verbose
        if verbose:
            print("Create Ideal Capacitor.")
            
        self.log_full = config['log'] if 'log' in config else False
        self.capacitance = config['capacitance']
        self.voltage_rated = config['v_rated']
        self.voltage_initial = config['v_initial'] if 'v_initial' in config else 0
        
        self.time_base = time_base
        
        
    def reset(self):
        self.voltage = self.voltage_initial
        self.log_dict = {'time' : 0, 'event' : CapacitorEvent.SUCCESS, 'voltage' : self.voltage, 'leakage' : 0}
        self.log = [self.log_dict.copy()]
        self.stats = {'energy_leaked' : 0}
        self.log_processed = False

    def set_voltage(self, v):
        self.voltage = v
        
    def get_voltage(self):
        return self.voltage
        
    def charge_fully(self):
        self.voltage = self.voltage_rated
        
    def discharge_fully(self):
        self.voltage = 0
        
    def get_leakage(self, i = 0):
        return 0

    def update_state(self, time, dt, i): #charge_discharge
        
        i = i - self.get_leakage(i)
        self.voltage += (i * (dt * self.time_base)) / self.capacitance
                
        if self.voltage > self.voltage_rated:
            self.log_dict['event'] = CapacitorEvent.OVERVOLTAGE
        
        if self.voltage < 0:
            self.voltage = 0
            self.log_dict['event'] = CapacitorEvent.EMPTY
            
        if self.log_full: 
            self.log_dict['voltage'] = self.voltage
            self.log_dict['time'] = (time + dt) * self.time_base
            self.log_dict['leakage'] = self.get_leakage()
            self.log_dict['i_in'] = i
            self.log.append(self.log_dict.copy())
        
        self.stats['energy_leaked'] = self.stats['energy_leaked'] + i*self.voltage*dt*self.time_base
    
    #Compute when we would cross the voltage threshold considering constant i     
    def get_next_change(self, i, voltage_threshold): 
        i = i - self.get_leakage(i)
        # we will never reach this threshold
        if (i == 0) or (voltage_threshold == None) or (i < 0 and voltage_threshold > self.voltage) \
            or (i > 0 and voltage_threshold < self.voltage):
                return None
            
        next_change = int((self.capacitance * (voltage_threshold - self.voltage) / i) / self.time_base)
        return next_change if next_change != 0 else None 
    
    def process_log(self, time_max):
        if self.log_full:
            self.log = pd.DataFrame(self.log)
            self.log.loc[:,'dt'] = abs(self.log.time.diff(-1))
            self.log.loc[self.log.index[-1], 'dt'] = time_max*self.time_base - self.log.time.iloc[-1]
        else:
            self.log = pd.DataFrame()
        self.log_processed = True
            
    def get_log(self):
        if not self.log_processed:
            self.process_log()
        
        return self.log
    
    def get_log_stats(self, normalize):
        return self.stats
