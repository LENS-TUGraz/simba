# -*- coding: utf-8 -*-
"""
Converter module implementation:

Buck-Boost converter

The `BuckBoost` module describes a converter structure, 
where the boost- and buck-converter stages can be configured arbitrarily. 
For both converters, the voltage and efficiencies can be set accordingly. 
If the input/output voltage is not configured or set to zero, 
it is assumed that no converter is used 
(e.g., `Vout = Vcap` + `Eout = 1` or `Vin = Vcap`+ `Ein = 1`).

This model also implements an overvoltage protection of the capacitor, i.e., 
the input efficiency is set to 0 if `VCap` > `v_ov`, and the quiescent current of the converter(s) can be configured.
"""

import pandas as pd
from VoltageMonitor import VoltageMonitor

class BuckBoost:
    
    def __init__(self, config, verbose, time_base):
        self.verbose = verbose
        if verbose:
            print("Create model of Buck converter.") 
        self.time_base = time_base    
        # Set logging
        self.log_full = config['log'] if 'log' in config else True
            
        # Configurable parameters 
        self.v_out = config['v_out'] if 'v_out' in config else 0
        self.v_in = config['v_in'] if 'v_in' in config else 0
        self.out_efficiency = config['efficiency_out'] if 'efficiency_out' in config else 1
        self.in_efficiency =  config['efficiency_in'] if 'efficiency_in' in config else 1
        self.i_quiescent = config['i_quiescent'] if 'i_quiescent' in config else 0
        self.v_ov = config['v_ov']
        self.voltage_monitor = VoltageMonitor([])
                           
    def reset(self, voltage, harvester_ocv): #todo: logging
        pass
    
    def get_input_operating_voltage(self, cap_voltage, harvester_ocv, time):
        if self.v_in == 0 or cap_voltage < self.v_in:
            return cap_voltage
        else:
            return self.v_in
    
    def get_input_efficiency(self, voltage, current):
        if voltage >= self.v_ov:
            return 0
        else:
            return self.efficiency_in
        
    def get_output_efficiency(self, cap_voltage, current):
        return self.efficiency_out
    
    def get_output_operating_voltage(self, cap_voltage):
        if self.v_out == 0 or cap_voltage < self.v_out:
            return cap_voltage
        
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