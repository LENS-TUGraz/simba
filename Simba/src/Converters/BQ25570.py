# -*- coding: utf-8 -*-
"""
Converter module implementation:

BQ25570

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
    
class BQ25570:
    
    class BQ255xxState(Enum):
        COLDSTART = 0
        UNDERVOLTAGE = 1
        CHARGING = 2
        OVERVOLTAGE = 3
    
    def __init__(self, config, verbose, time_base):
        self.verbose = verbose
        if verbose:
            print("Create model of BQ25570 converter.")
        self.time_base = time_base   
        # Set loggging
        self.log_full = config['log'] if 'log' in config else False
            
        # Configurable parameters (by resistor network)
        self.v_out = config['v_out']
        self.mpp = config['mpp']    #In range 0-1
        self.v_ov = config['v_ov']
        
        self.v_out_enable_treshold_high = config['vout_ok_high'] if 'vout_ok_high' in config else 0
        self.v_out_enable_treshold_low = config['vout_ok_low'] if 'vout_ok_low' in config else 0
        self.enable_hysteresis = config['vout_ok_enable'] if 'vout_ok_enable' in config else False
        
        self.bypass_boost_converter = config['bypass_boost_converter'] if 'bypass_boost_converter' in config else False
        
        #Internal parameters
        self.v_chgen = config['v_chgen'] if 'v_chgen' in config else 1.8 
        self.v_uv = config['v_uv'] if 'v_uv' in config else 1.95 
        
        #Should be stated only if the capacitor is precharged otherwise boostconverter will start with a very low efficiency in the first MPPT interval
        self.harvester_default_ocv = config['initial_ocv'] if 'initial_ocv' in config else 0.5
        
        
        #create voltage manager to inform simulation about time of threshold crossing
        thresholds = [("OUTPUT_OFF", self.v_ov, "both"),
                      ("OUTPUT_ON", self.v_chgen, "both"),
                      ("COLD_START", self.v_uv, "both"),
                      ("COLD_START", self.v_out_enable_treshold_high, "both"),
                      ("COLD_START", self.v_out_enable_treshold_low, "both")]
        self.voltage_monitor = VoltageMonitor(thresholds)
        
        
        #Load Boost converter data, Columns: Vin, Vstor, Iin, Efficiency
        file_name = os.path.join(os.path.dirname(__file__), "converter_data", "BQ25570", f"boostConverterData.npy")
        self.boostconverter_data = np.load(file_name)
        
        #Load Buck converter data. Columns:Vstor, Iout, Efficiency
        availaible_v_out = [1.8, 2.0, 2.2, 2.4, 3.0, 3.3]
        if self.v_out not in availaible_v_out:
            print("Selected v_out is not within available values.\nFollowing values are selectable:")
            print(availaible_v_out)
            print("Terminting")
            sys.exit()
        
        file_name = os.path.join(os.path.dirname(__file__), "converter_data", "BQ25570", "buckConverterData_vout=" + str(self.v_out) + ".npy")
        self.buckconverter_data = np.load(file_name)
        
        #Load quiescent current data. Columns:Vstor, Iquiescent
        file_name = os.path.join(os.path.dirname(__file__), "converter_data", "BQ25570", "quiescentData_activeMode.npy")
        self.quiescent_data_activeMode = np.load(file_name)
        
        file_name = os.path.join(os.path.dirname(__file__), "converter_data", "BQ25570", "quiescentData_standbyMode.npy")
        self.quiescent_data_standbyMode = np.load(file_name)
    
        
    def reset(self, cap_voltage, harvester_ocv):
        self.v_stor = cap_voltage
        self.next_ocv_sampling = 0.0
        self.harvester_ocv = harvester_ocv
        self.vout_on = True if cap_voltage > self.v_out_enable_treshold_high else False
        
        self.voltage_old = None
        self.voltage_in_old = None
        self.current_in_old = None
        self.current_out_old = None
        
        self.log = [{'time' : 0, 
                     'v_stor' : self.v_stor,
                     'state' : self.get_state()}]
        self.log_processed = False


    def turn_off(self, cap_voltage):
        if cap_voltage < self.v_high: #we would never turn on again otherwise
            self.on = False

    def get_input_operating_voltage(self, cap_voltage, harvester_ocv, time):
        
        if self.bypass_boost_converter:
            return cap_voltage
        
        match self.get_state():
            case self.BQ255xxState.COLDSTART:
                #When chip gets into coldstart the ic is turned off and parameters turn to default
                #The simulator simplifies v_stor=vcap, in reallity in coldstart: v_stor-0.3=vcap
                #This can be easily used here for a more realistic MPPT behaviour
                if self.v_stor < self.v_chgen - 0.3:
                    self.harvester_ocv = self.harvester_default_ocv
                    self.next_ocv_sampling = 0
                return 0.33  #Vin is clamped to 0.33V at coldstart according to measurements
            case self.BQ255xxState.CHARGING | self.BQ255xxState.UNDERVOLTAGE:
                #self.sample_ocv(harvester_ocv, time)
                return self.harvester_ocv * self.mpp
            case self.BQ255xxState.OVERVOLTAGE:
                #self.sample_ocv(harvester_ocv, time)
                return 0.0  #Vin is pulled to ground on overvoltage
    
    def get_output_operating_voltage(self, cap_voltage):
        match self.get_state():
            case self.BQ255xxState.COLDSTART | self.BQ255xxState.UNDERVOLTAGE:
                return 0.0
            case self.BQ255xxState.CHARGING | self.BQ255xxState.OVERVOLTAGE:
                return min(cap_voltage, self.v_out) if self.vout_on else 0.0
    
    def get_input_efficiency(self, voltage, current):
        
        if self.bypass_boost_converter:
            return 1.0
        
        match self.get_state():
            case self.BQ255xxState.COLDSTART:
                #Coldstart efficiency does not seem to depend on voltage or current, this value is the average of our measurements
                return 0.06    
            case self.BQ255xxState.CHARGING | self.BQ255xxState.UNDERVOLTAGE:
                return self.get_boostconverter_efficiency(voltage, current)
            case self.BQ255xxState.OVERVOLTAGE:
                return 1.0
    
    def get_output_efficiency(self, cap_voltage, current):
        match self.get_state():
            case self.BQ255xxState.COLDSTART | self.BQ255xxState.UNDERVOLTAGE:
                #Output voltage is 0 in this state
                return 1.0
            case self.BQ255xxState.CHARGING | self.BQ255xxState.OVERVOLTAGE:
                return self.get_buckconverter_efficiency(cap_voltage, current)
            
    def get_quiescent(self, voltage):
        match self.get_state():
            case self.BQ255xxState.COLDSTART:
                #Chip is disabled while in coldstart
                return 0.0
            case self.BQ255xxState.UNDERVOLTAGE:
                #Standby mode with lower quiescent current
                index = take_closest(self.quiescent_data_standbyMode[:, 0], voltage, True)
                return self.quiescent_data_standbyMode[index][1]
            case self.BQ255xxState.CHARGING | self.BQ255xxState.OVERVOLTAGE:
                #Active mode with buck converter enabled
                index = take_closest(self.quiescent_data_activeMode[:, 0], voltage, True)
                return self.quiescent_data_activeMode[index][1]
    
    def update_state(self, time, dt, cap_voltage):
        #According to plots in datasheet v_stor follows v_bat
        self.v_stor = cap_voltage
        
        if self.enable_hysteresis:
            if self.vout_on and cap_voltage <= self.v_out_enable_treshold_low:
                self.vout_on = False
            elif not self.vout_on and cap_voltage >= self.v_out_enable_treshold_high:
                self.vout_on = True
                
        if self.log_full:
            self.log.append({'time' : time * self.time_base, 
                             'v_stor' : self.v_stor,
                             'state' : self.get_state()})
    
    def process_log(self, time_max):
        if self.log_full:
            self.log = pd.DataFrame(self.log)
            self.log.loc[:, 'dt'] = abs(self.log.time.diff(-1))
            self.log.loc[self.log.index[-1],'dt'] = time_max*self.time_base - self.log.time.iloc[-1]
        else:
            self.log = pd.DataFrame()
        self.log_processed = True
    
    def get_log(self):
        if not self.log_processed:
            self.process_log(0)
        
        return self.log
    
    def get_next_change(self): 
        if self.next_ocv_sampling != 0:
            return self.next_ocv_sampling
        else:
            return None
    
    def get_state(self):
        if self.v_stor < self.v_chgen:
            return self.BQ255xxState.COLDSTART
        elif self.v_stor < self.v_uv:
            return self.BQ255xxState.UNDERVOLTAGE
        elif self.v_stor < self.v_ov:
            return self.BQ255xxState.CHARGING
        else:
            return self.BQ255xxState.OVERVOLTAGE
    
    
    def get_buckconverter_efficiency(self, voltage_in, current_out):
       
    
        if voltage_in == 0.0 or current_out == 0.0:
            return 1.0
        
        # we update only on changes
        if self.voltage_in_old != voltage_in or self.current_out_old != current_out:
        
            #Find closest value in column 1 (Iout)
            closest_current_idx_min = take_closest(self.buckconverter_data[:, 1], current_out, True)
    
            #Take all rows with same current value (current influences buck efficency the most)
            closest_current_idx_max = bisect_right(self.buckconverter_data[:, 1], self.buckconverter_data[closest_current_idx_min][1]) - 1
            search_data = self.buckconverter_data[closest_current_idx_min:closest_current_idx_max]
    
            #Take row with closest v_stor
            closest_index = take_closest(search_data[:, 0], voltage_in, True)
            
            self.buck_eff = search_data[closest_index][2]
            self.voltage_in_old = voltage_in
            self.current_out_old = current_out
        
        return self.buck_eff
        
        
    def get_boostconverter_efficiency(self, voltage, current_in):
        if voltage == 0.0 or current_in == 0.0:
            return 1.0
        
        # we update only on changes
        if self.voltage_old != voltage or self.current_in_old != current_in:
        
            #Boostcharger data is in micro amps
            current_micro = current_in * 1000000 
            
            #Find closest value in column 1 (Iout)
            closest_current_idx_min = take_closest(self.boostconverter_data[:, 2], current_micro, True)
            closest_current_idx_max = bisect_right(self.boostconverter_data[:, 2], self.boostconverter_data[closest_current_idx_min][2]) - 1
    
            #Compute absolute error for all datapoints within range
            self.close_data = self.boostconverter_data[closest_current_idx_min:closest_current_idx_max]
            self.error_data = abs(voltage - self.close_data[:,0]) + abs(self.v_stor - self.close_data[:,1])
            self.min_error_index = np.where(self.error_data == self.error_data.min())[0][0]
            
            #Return efficiency in range 0-1
            self.boost_eff = self.close_data[self.min_error_index][3] / 100
            self.voltage_old = voltage
            self.current_in_old = current_in
            
        return self.boost_eff

    def sample_ocv(self, harvester_ocv, time):
        if self.next_ocv_sampling == 0:
            self.next_ocv_sampling = time + int(16/self.time_base)
        elif time >= self.next_ocv_sampling:
            self.next_ocv_sampling = time + int(16/self.time_base)
            self.harvester_ocv = harvester_ocv
            
    def get_log_stats(self, normalize):
        pass