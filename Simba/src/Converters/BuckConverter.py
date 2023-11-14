# -*- coding: utf-8 -*-
"""
Converter module implementation:

Buck converter

TODO: description
"""

import pandas as pd
from enum import Enum
import os
import numpy as np
from bisect import bisect_right
import sys
from Helper import take_closest
from VoltageMonitor import VoltageMonitor

class BuckConverter:
    
    def __init__(self, config, verbose, time_base):
        self.verbose = verbose
        if verbose:
            print("Create model of Buck converter.") 
        self.time_base = time_base    
        # Set loggging
        self.log_full = config['log'] if 'log' in config else True
            
        # Configurable parameters 
        self.v_out = config['v_out']
        self.v_ov = config['v_ov']
        self.efficiency = config['efficiency']
        self.i_quiescent = config['i_quiescent']
                
        self.voltage_monitor = VoltageMonitor([])
        
                   
    def reset(self, voltage, harvester_ocv): #todo: logging
        pass
    
    def get_input_operating_voltage(self, cap_voltage, harvester_ocv, time):
        return cap_voltage
    
    def get_input_efficiency(self, voltage, current):
        if voltage >= self.v_ov:
            return 0
        else:
            return 1.0
        
    def get_output_efficiency(self, cap_voltage, current):
        return self.efficiency
    
    def get_output_operating_voltage(self, cap_voltage):
        if cap_voltage < self.v_out:
            return cap_voltage
        
        if cap_voltage > self.v_ov:
            return self.v_ov
        
        return self.v_out
    
    def turn_off(self, cap_voltage):
        pass

    
    def get_quiescent(self, cap_voltage):
        return self.i_quiescent
    
    def update_state(self, time, dt, cap_voltage): #todo: logging
        pass
    
    def process_log(self):  #todo: logging
        pass
    
    def get_log(self): #todo: logging
        return pd.DataFrame()
    
    def get_log_stats(self, normalize):
        pass