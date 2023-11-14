# -*- coding: utf-8 -*-
"""
Converter module implementation:

Diode

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

class Diode:
    #TODO: voltage drop
    def __init__(self, config, verbose, time_base):
        self.verbose = verbose
        if verbose:
            print("Create model of Diode converter with overvoltage protection.")
        self.time_base = time_base
        self.v_ov = config['v_ov']
        self.i_quiescent = config['i_quiescent'] if 'i_quiescent' in config else 0
        self.voltage_monitor = VoltageMonitor([])
        
    
    def reset(self, cap_voltage, harvester_ocv): #todo: logging
        pass 
    
    def get_input_operating_voltage(self, cap_voltage, harvester_ocv, time):
        return cap_voltage
    
    def get_input_efficiency(self, voltage, current):
        if voltage >= self.v_ov:
            return 0
        else:
            return 1.0
        
    def get_output_efficiency(self, cap_voltage, current):
        return 1.0
    
    def get_output_operating_voltage(self, cap_voltage):
        return cap_voltage
    
    def get_quiescent(self, cap_voltage):
        return self.i_quiescent
    
    def get_voltage_thresholds(self):
        return []
    
    def update_state(self, time, dt, cap_voltage): #todo: logging
        pass
    
    def process_log(self):  #todo: logging
        pass
    
    def get_log(self): #todo: logging
        return pd.DataFrame()
    
    def get_log_stats(self, normalize):
        pass
