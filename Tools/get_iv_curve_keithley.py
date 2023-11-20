# -*- coding: utf-8 -*-
"""
Script to automatically obtain an IV curve using the Keithley2450 sourcemeter.
"""

import time
import numpy as np
import pandas as pd

from pymeasure.instruments.keithley import Keithley2450

# Specify sourcemeter source, the desired name of your solarpanel and the applied illuminance.
sourcemeter = Keithley2450('USB0::0x05E6::0x2450::04456242::0::INSTR') #Adjust accordingly
panel= 'Gameboy'
lux = 300
filename = f'{panel}_lux{lux}.json'
voltage_steps = 0.05

#%% Measure open circuit voltage first

sourcemeter.source_current = 0           # Set voltage
sourcemeter.apply_current(None, 10)      # Sets the compliance voltage to 3.5 V
sourcemeter.enable_source()              # Enables the source output
time.sleep(1)                            # Let the node start

sourcemeter.measure_voltage()
print(f"Voc: {sourcemeter.voltage}")
v_oc = sourcemeter.voltage
current_limit = 10e-3

#Disable and move on to next current
sourcemeter.disable_source()

#%% Measure IV curve from 0.1 to VOC

# Dummy measurement first
sourcemeter.source_voltage = 0.1                  # Set voltage
sourcemeter.apply_voltage(20, current_limit)      # Sets the compliance voltage to 3.5 V
sourcemeter.current_range = current_limit
sourcemeter.enable_source()                         # Enables the source output

time.sleep(1)                                       # Let the node start
sourcemeter.measure_current(current=current_limit, auto_range=False)

#Disable and move on to next current
sourcemeter.disable_source()

#Let's get the curve and store it
iv = {}
testVoltages = np.arange(0.1, v_oc, voltage_steps) # in V
for voltage in testVoltages:

    print(f'Measure current at {voltage} V.') 
    #Set current at sourcemeter accordingly
    sourcemeter.source_voltage = voltage              # Set voltage
    sourcemeter.apply_voltage(20, current_limit)      # Sets the compliance voltage to 3.5 V
    sourcemeter.current_range = current_limit
    sourcemeter.enable_source()                         # Enables the source output
    
    time.sleep(1)                                       # Let the node start
    
    sourcemeter.measure_current(current=current_limit, auto_range=False)
    print(voltage, sourcemeter.current)
    
    iv[voltage] = sourcemeter.current
    
    #Disable and move on to next current
    sourcemeter.disable_source()
  
sourcemeter.adapter.close()

iv[v_oc] = 0
iv_pd = pd.DataFrame(iv, index=[0]).T
iv_pd.plot()
iv_pd.to_json(filename)
