# -*- coding: utf-8 -*-
"""
Converter module implementation:

LDO

The `LDO` module describes a converter structure, where a *linear low-dropout regulator* is placed 
between capacitor and load to convert the capacitor voltage to a fixed output voltage (i.e., `Vout = X`) 
by dissipating the difference between input/output voltage as waste heat (i.e., `Eout = Vout/Vcap`). 
In this configuration, there is no converter between harvester and capacitor (i.e., `Vin = Vcap`, `Ein = 1`). 

Additionally, this converter module can optionally model a *hysteresis behavior*, 
where the output is switches on/off at pre-defined voltage thresholds.
"""

import pandas as pd
from VoltageMonitor import VoltageMonitor

class LDO:
    
    def __init__(self, config, verbose, time_base):
        self.verbose = verbose
        if verbose:
            print("Create model of LDO converter.") 
        self.time_base = time_base    
        # Set logging
        self.log_full = config['log'] if 'log' in config else True
            
        # Configurable parameters 
        self.v_out = config['v_out']
        self.i_quiescent = config['i_quiescent'] if 'i_quiescent' in config else 0
        self.i_quiescent_off = config['i_quiescent_off'] if 'i_quiescent_off' in config else self.i_quiescent
        
        if 'enable_hyst' in config and config['enable_hyst'] == True:
            self.hysteresis = True
            self.v_high = config['v_high']
            self.v_low = config['v_low']
        
            thresholds = [("ON", config['v_high'], "rising"),
                          ("OFF", config['v_low'], "falling"),
                          ("OUT", config['v_out'], "both")]
        else:
            thresholds = [("OUT", config['v_out'], "both")]
            self.hysteresis = False
        
        self.voltage_monitor = VoltageMonitor(thresholds) #create voltage manager to inform simulation about time of threshold crossing
        
    def reset(self, cap_voltage, harvester_ocv): #todo: logging
        if self.hysteresis:
            if cap_voltage >= self.v_low:
                self.on = True
            else:
                self.on = False
        else: 
            self.on = True
    
    def turn_off(self, cap_voltage):
        if cap_voltage < self.v_high: #we would never turn on again otherwise
            self.on = False
     
    def get_input_operating_voltage(self, cap_voltage, harvester_ocv, time):
        return cap_voltage
    
    def get_input_efficiency(self, voltage, current):
        return 1.0
        
    def get_output_efficiency(self, cap_voltage, current):
        if cap_voltage > self.v_out:
            return self.v_out / cap_voltage
        else:
            return 1.0
    
    def get_output_operating_voltage(self, cap_voltage):
        if self.on:
            return min(cap_voltage, self.v_out)
        else:
            return 0.0

    def get_quiescent(self, cap_voltage):
        if self.on:
            return self.i_quiescent
        else:
            return self.i_quiescent_off
    
    
    def update_state(self, time, dt, cap_voltage): #todo: logging
        if self.hysteresis:
            if self.on and cap_voltage < self.v_low:
                self.on = False
            elif not self.on and cap_voltage > self.v_high:
                self.on = True
    
    def process_log(self):  #todo: logging
        pass
    
    def get_log(self): #todo: logging
        return pd.DataFrame()
    
    def get_log_stats(self, normalize):
        pass
    
  