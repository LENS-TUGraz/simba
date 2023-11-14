# -*- coding: utf-8 -*-
"""
Converter module implementation:

Hysteresis

Todo: description
"""

import pandas as pd
from enum import Enum
import os
import numpy as np
from bisect import bisect_right
import sys
from Helper import take_closest
from VoltageMonitor import VoltageMonitor
    
class Hysteresis:

    def __init__(self, config, verbose, time_base):
        self.verbose = verbose
        if verbose:  
            print("Create model of Hysteresis converter with overvoltage protection.")
        self.time_base = time_base
        self.v_ov = config['v_ov']
        self.v_high = config['v_high']
        self.v_low = config['v_low']
        self.i_quiescent = config['i_quiescent'] if 'i_quiescent' in config else 0
        self.i_quiescent_off = config['i_quiescent_off'] if 'i_quiescent_off' in config else self.i_quiescent
        
        thresholds = [("ON", config['v_high'], "rising"),
                      ("OFF", config['v_low'], "falling")]
        self.voltage_monitor = VoltageMonitor(thresholds) #create voltage manager to inform simulation about time of threshold crossing
    
    def reset(self, cap_voltage, harvester_ocv): #todo: logging
        if cap_voltage >= self.v_low:
            self.on = True
        else:
            self.on = False
            
    def turn_off(self, cap_voltage):
        if cap_voltage < self.v_high:
            self.on = False
    
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
        if self.on:
            return cap_voltage
        else:
             return 0.0

    
    def get_quiescent(self, cap_voltage):
        if self.on:
            return self.i_quiescent
        else:
            return self.i_quiescent_off
    
    
    def update_state(self, time, dt, cap_voltage): #todo: logging
        if self.on and cap_voltage <= self.v_low:
            self.on = False
        elif not self.on and cap_voltage >= self.v_high:
            self.on = True
    
    def process_log(self):  #todo: logging
        pass
    
    def get_log(self): #todo: logging
        return pd.DataFrame()
    
    def get_log_stats(self, normalize):
        pass
    
