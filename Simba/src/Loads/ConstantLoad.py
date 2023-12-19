# -*- coding: utf-8 -*-
"""
Load module implementation:

ConstantLoad

The `ConstantLoad` module represents a load that draws a constant current.
"""

from VoltageMonitor import VoltageMonitor
from aenum import Enum
import pandas as pd

class ConstantLoad:
    
    States = Enum("State", ['OFF', 'ON'])
    
    def __init__(self, config, verbose, time_base):
        self.current = config['current']
        self.log_full = config['log'] if 'log' in config else False
        self.voltage_monitor = VoltageMonitor([])
        self.reset(0, 0)
        self.time_base = time_base
    
    def reset(self, initial_voltage, initial_cap_voltage):
        self.state = self.States['ON'] 
        self.update_time = None
        
        self.log_processed = False
        self.log = [{'time' : 0, 
                     'i_out' : self.get_current(0), 
                     'state' : self.state.name,
                     'v_out' : initial_voltage}]

    def get_state(self):
        return self.state
    
    def set_state(self, state):
        self.state = state
             
    def get_current(self, voltage):
        if voltage == 0:
            return 0
        
        return self.current

    def get_next_change(self, time):
        return None

    def update_state(self, time, dt, input_voltage, cap_voltage):
        if self.log_full:
            self.log.append({'time' : time*self.time_base, 
                            'i_out' : self.get_current(input_voltage), 
                            'state' : self.state.name, 
                            'v_out' : input_voltage})
    
    def process_log(self, time_max):
        if self.log_full:
            self.log = pd.DataFrame(self.log)
            self.log.loc[:, 'dt'] = abs(self.log.time.diff(-1))
            self.log.loc[self.log.index[-1],'dt'] = time_max*self.time_base - self.log.time.iloc[-1]
            self.log.loc[:,'p_out'] = self.log.i_out * (self.log.v_out.shift(-1) + self.log.v_out)/2 #interpolate/estimate power consumption between two different voltage points
        self.log_processed = True
    
    def get_log(self):  
        if not self.log_processed:
            self.process_log()
    
        return self.log