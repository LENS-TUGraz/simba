# -*- coding: utf-8 -*-
"""
Created on Tue Apr 18 14:37:44 2023

Based on: http://lampx.tugraz.at/~hadley/semi/ch9/instruments/Keithley26xx/Keithley26xx.php
"""
import pyvisa
import time

class SMUChannel:
    
    def __init__(self, channel, smu):
        self.channel = channel
        self.smu = smu
        
        self.__voltage_range = 20
        self.__current_range = 2
        
        
    def set_mode_voltage_source(self):
        """
        Sets the channel into voltage source mode.
        In this mode you set the voltage and can measure current, resistance and power.
        """
        self.smu._set_source_mode(self.channel, KeysightB2900.VOLTAGE_MODE)

    def set_mode_current_source(self):
        """
        Sets the channel into current source mode.
        In this mode you set the current and can measure voltage, resistance and power.
        """
        self.smu._set_source_mode(self.channel, KeysightB2900.CURRENT_MODE)

    def set_voltage_limit(self, value):
        """
        Limits the voltage output of the current source.
        If you are in voltage source mode the voltage limit has no effect.
        """
        if value <= self.__voltage_range:
            self.smu._set_limit(self.channel, KeysightB2900.VOLTAGE_MODE, value)
        else:
            raise ValueError("The limit is not within the range. Please set the range first")

    def set_current_limit(self, value):
        """
        Limits the current output of the voltage source.
        If you are in current source mode the current limit has no effect.
        """
        if value <= self.__current_range:
            self.smu._set_limit(self.channel, KeysightB2900.CURRENT_MODE, value)
        else:
            raise ValueError("The limit is not within the range. Please set the range first")

    
    def set_voltage(self, value):
        """
        Sets the output level of the voltage source.
        """
        self.smu._set_level(self.channel, KeysightB2900.VOLTAGE_MODE, value)

    def set_current(self, value):
        """
        Sets the output level of the current source.
        """
        self.smu._set_level(self.channel, KeysightB2900.CURRENT_MODE, value)
        
    def set_current_measure_range(self, value):
        """
        Disables AUTO range function and sets measurement range for current measurements
        """
        self.smu._set_measurement_range_mode(self.channel, KeysightB2900.CURRENT_MODE, 'OFF')
        self.smu._set_measurement_range_fixed(self.channel, KeysightB2900.CURRENT_MODE, value)

    def set_voltage_measure_range(self, value):
        """
        Disables AUTO range function and sets measurement range for voltage measurements
        """
        self.smu._set_measurement_range_mode(self.channel, KeysightB2900.VOLTAGE_MODE, 'OFF')
        self.smu._set_measurement_range_fixed(self.channel, KeysightB2900.VOLTAGE_MODE, value)

    def enable_output(self):
        """
        Sets the source output state to on.

        Note:
           When the output is switched on, the SMU sources either voltage or current, as set by
           set_mode_voltage_source() or set_mode_current_source()
        """
        self.smu._set_output_state(self.channel, KeysightB2900.STATE_ON)

    def disable_output(self):
        """
        Sets the source output state to off.

        Note:
           When the output is switched off, the SMU goes in to low Z mode (meaning: the output is shorted).
           Be careful when using the SMU for measurement of high power devices. The disabling of the output could lead
           high current flow.
        """
        self.smu._set_output_state(self.channel, KeysightB2900.STATE_OFF)
        
    def output_off_state_highz(self):
        """
        Sets the source output to HIGH-Z if turned off.
        """
        self.smu._set_off_state(self.channel, KeysightB2900.OUTPUT_OFF_HIGHZ)
        
    def output_off_state_normal(self):
        """
        Sets the source output to Normal if turned off.
        """
        self.smu._set_off_state(self.channel, KeysightB2900.OUTPUT_OFF_NORMAL)
        
    def output_off_state_zero(self):
        """
        Sets the source output to ZERO (short) if turned off.
        
        Note: Be careful, there might be high currents if you short the output!
        """
        self.smu._set_off_state(self.channel, KeysightB2900.OUTPUT_OFF_ZERO)
        
        
    def measure_voltage(self):
        """
        Perform spot measurement and retrieve voltage.

        Note:
           When the output is switched off, the SMU turns on output automatically and performs a measurement.
        """
        return self.smu._measure(self.channel, KeysightB2900.VOLTAGE_MODE)
    
    def measure_current(self):
        """
        Perform spot measurement and retrieve current.

        Note:
           When the output is switched off, the SMU turns on output automatically and performs a measurement.
        """
        return self.smu._measure(self.channel, KeysightB2900.CURRENT_MODE)
    
    def perform_time_sweep_current_source(self, current_value, current_value_start, voltage_limit, points, interval, disable = True, set_range = True):
        """
        Perform time domain measurement with constant sourced current retrieve <num_points> measurements with a certain <interval>.
        """
        return self.smu._time_domain_sweep(self.channel, KeysightB2900.CURRENT_MODE, current_value, current_value_start, voltage_limit, points, interval, disable, set_range)
      
    def perform_time_sweep_voltage_source(self, voltage_value, voltage_level_start, current_limit, points, interval, disable = True, set_range = True):
        """
        Perform time domain measurement with constant sourced current retrieve <num_points> measurements with a certain <interval>.
        """
        return self.smu._time_domain_sweep(self.channel, KeysightB2900.VOLTAGE_MODE, voltage_value, voltage_level_start, current_limit, points, interval, disable, set_range)
      
    

class KeysightB2900: 
    
    dev = None
    dev_id = ""
    
    # define strings that are used in the LUA commands
    CHAN1 = "2"
    CHAN2 = "1"

    CURRENT_MODE = "CURR"
    VOLTAGE_MODE = "VOLT"

    STATE_ON = "ON"
    STATE_OFF = "OFF"
    
    OUTPUT_OFF_ZERO = "ZERO"
    OUTPUT_OFF_HIGHZ = "HIZ"
    OUTPUT_OFF_NORMAL = "NORM"

    SPEED_FAST = 0.01
    SPEED_MED = 0.1
    SPEED_NORMAL = 1
    SPEED_HI_ACCURACY = 10
    
    
    
    def __init__(self, dev_addr = "USB0::2391::12345::XY00001234::0::INSTR"):
        rm = pyvisa.ResourceManager()

        self.dev = rm.open_resource(dev_addr)
        self.dev.clear()
        self.dev_id = self.dev.query("*IDN?")
        
        assert "B2902B" in self.dev_id, "Error: Unexpected device found."
        
        self.chan1 = SMUChannel("1", self)
        self.chan2 = SMUChannel("2", self)
        

    def close(self):
        if self.dev != None:
            self.dev.close()
            self.dev = None
    
    def reset(self):
        
        if self.dev == None:
            raise RuntimeError("Device not connected.")
            
        self.dev.write("*RST")
        
    def set_display(self):
        #todo
        pass
    
        
    def write_command(self, command):
        
        if self.dev == None:
            raise RuntimeError("Device not connected.")
            
        self.dev.write(command)
        
    def write_query(self, query):
        
        if self.dev == None:
            raise RuntimeError("Device not connected.")
            
        data = self.dev.query(query)  
        return data
    
    
    """
    #####################################################################################
    commands for setting the parameters of channels
    those should not be accessed directly but through the channel class
    #####################################################################################
    """


    def _set_off_state(self, channel, off_state):
        """defines how the output reacts if the channel is turned off (e.g., HIGH-Z, Short etc.)"""
        cmd = f':OUTP{channel}:OFF:MODE {off_state}'
        self.write_command(cmd)

    def _set_measurement_speed(self, channel, speed, sense_mode):
        """defines how many PLC (Power Line Cycles) a measurement takes"""
        cmd = f':SENS{channel}:{sense_mode}:NPLC {speed}'
        self.write_command(cmd)

    def _set_source_mode(self, channel, source_mode):
        cmd = f':SOUR{channel}:FUNC:MODE {source_mode}'
        self.write_command(cmd)

    def _set_sense_wire_mode(self, channel, four_wire_on):
        """set 2-wire or 4-wire sense mode"""
        cmd = f':SENS{channel}:REM {four_wire_on}'
        self.write_command(cmd)

    def _set_limit(self, channel, sense_mode, value):
        """command used to set the limits for voltage or current"""
        cmd = f':SENS{channel}:{sense_mode}:PROT {value}'
        self.write_command(cmd)

    def _set_level(self, channel, source_mode, value):
        cmd = f':SOUR{channel}:{source_mode} {value}'
        self.write_command(cmd)

    def _set_output_state(self, channel, on_off):
        cmd = f':OUTP{channel} {on_off}'
        self.write_command(cmd)  
      
    def _set_measurement_range_mode(self, channel, sense_mode, auto):
        cmd = f':SENS{channel}:{sense_mode}:RANG:AUTO {auto}'
        self.write_command(cmd)
     
    def _set_measurement_range_fixed(self, channel, sense_mode, value): 
        cmd = f':SENS{channel}:{sense_mode}:RANG {value}'
        self.write_command(cmd)
     
    def _set_measurement_range_upper_limit(self, channel, sense_mode, lower_limit):
        cmd = f':SENS{channel}:{sense_mode}:RANG:AUTO:ULIM {lower_limit}'
        self.write_command(cmd)
        
    def _set_measurement_range_lower_limit(self, channel, sense_mode, upper_limit):
        cmd = f':SENS{channel}:{sense_mode}:RANG:AUTO:ULIM {upper_limit}'
        self.write_command(cmd)
            
    """
    #####################################################################################
    commands for reading values from the channels
    those should not be accessed directly but through the channel class
    #####################################################################################
    """
    
    def _measure(self, channel, mode):
        query = f'MEAS:{mode}? (@{channel})'
        result = self.dev.query(query).strip("\n")
        
        return float(result)
        
    def _time_domain_sweep(self, channel, source_mode, source_value, source_value_start, sense_limit, num_points, interval, disable, set_range):
        
        if interval < 20e-6:
            print("Warning: Minimum sampling interval is 20us.")
            interval = 20e-6
        
        sense_mode = self.CURRENT_MODE if source_mode == self.VOLTAGE_MODE else self.VOLTAGE_MODE
        
        
        # Config source and sensing limit
        self.write_command(f":SOUR{channel}:FUNC:MODE {source_mode}")
        self.write_command(f":SOUR{channel}:{source_mode} {source_value_start}")
        self.write_command(f":SENS{channel}:FUNC '{sense_mode}'")    
        self.write_command(f":SENS{channel}:{sense_mode}:PROT {sense_limit}")
        self.write_command(f":SOUR{channel}:{source_mode}:MODE SWE")
        self.write_command(f":SOUR{channel}:SWE:SPAC LIN")
        self.write_command(f":SOUR{channel}:{source_mode}:STAR {source_value}")
        self.write_command(f":SOUR{channel}:{source_mode}:STOP {source_value}")
        self.write_command(f":SOUR{channel}:{source_mode}:POIN 1")
        
        if set_range:
            print("Set range")
            self.write_command(":SENS{channel}:{sense_mode}:RANG:AUTO:LLIM {sense_limit}")
            self.write_command(":SOUR{channel}:{source_mode}:RANG:AUTO:LLIM {source_value * 2}")
               
        # Config time triggering for sensing
        self.write_command(f":TRIG{channel}:SOUR TIM")
        self.write_command(f":TRIG{channel}:ACQ:TIM {interval}")
        self.write_command(f":TRIG{channel}:TRAN:COUN 1")
        self.write_command(f":TRIG{channel}:ACQ:COUN {num_points}")
        self.write_command(f":TRIG{channel}:TRAN:DEL 20e-6")
        self.write_command(f":TRIG{channel}:ACQ:DEL 0")
        
        #time.sleep(1)
        
        # Enable output and init measurement
        self.write_command(f":OUTP{channel} ON")        
        self.write_command(f":INIT (@{channel})")
        
        #Wait until measurement is complete (might run into timeout otherwise)
        time.sleep(num_points * interval + 1)
                
        self.dev.clear()
        
        # Retrieve data        
        times = self.write_query(f":FETCH:ARR:TIME? (@{channel})").strip("\n").split(',')
        current = self.write_query(f":FETCH:ARR:CURR? (@{channel})").strip("\n").split(',')
        voltage = self.write_query(f":FETCH:ARR:VOLT? (@{channel})").strip("\n").split(',')
        
        if disable:
            self.write_command(f":OUTP{channel} OFF")
            
        return times, current, voltage
        
               
