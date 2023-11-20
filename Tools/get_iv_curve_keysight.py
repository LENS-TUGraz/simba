"""
Script to automatically obtain an IV curve using the Keysight B2900 sourcemeter.
"""

from KeysightB2900 import KeysightB2900
import numpy as np
import time
import pandas as pd
import matplotlib.pyplot as plt

# Specify sourcemeter source, the desired name of your solarpanel and the applied illuminance.
ks = KeysightB2900('USB0::0xXXXX::0xXXXX::MYNAME::0::INSTR') #Adjust according to your SMU

panel= 'PanelName'
lux = 300
filename = f'{panel}_lux{lux}.json'
voltage_steps = 0.05
max_current = 10e-3


#TODO: measure V_OC first with sourcemeter
v_oc = 2.5

ks.chan1.disable_output()
ks.chan2.disable_output()

ks.chan1.set_mode_voltage_source()
ks.chan1.set_current_limit(max_current)
ks.chan1.set_voltage(0)
ks.chan1.enable_output()

iv = {}
testVoltages = np.arange(0.1, v_oc, voltage_steps) # in V
for voltage in testVoltages:

    ks.chan1.set_voltage(voltage)
    time.sleep(0.05)
    v = ks.chan1.measure_voltage()
	
    # Average over 100 samples
    i_list = []
    for cnt in range(0, 100):
        i_list.append(ks.chan1.measure_current() * (-1))
        
    i = np.mean(i_list)
    iv[voltage] = i

ks.chan1.disable_output()
ks.close()

iv[v_oc] = 0
iv_pd = pd.DataFrame(iv, index=[0]).T
iv_pd.plot()
iv_pd.to_json(filename)