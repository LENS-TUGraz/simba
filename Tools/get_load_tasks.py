# -*- coding: utf-8 -*-
"""
Tool to extract a load's task list automatically based on current traces from nRF PPK2:
This script extracts the (average) duration and (average) current consumption of each task
of a load under test. Each task must be indicated by a signal on separate GPIO lines.
"""

import time
import pandas as pd
import power_profiler
import argparse
import pprint

# Import list of task names (to map GPIO pin to name)
try:
  from task_names import task_names
except:
  print("Could not load task name list. Use GPIO pin numbers.")
  task_names = {"-1" : "INIT"}

def processInternalData(raw_data, sampling_rate = 100000):
    
    dt = 1/sampling_rate * 1000 #in ms

    currents = [val for currents_only in raw_data[0::2] for val in currents_only]
    gpios = [val for currents_only in raw_data[1::2] for val in currents_only]
    
    data = pd.DataFrame({'time' : [dt * i for i in range(0,len(currents))], 'current_uA' : currents, 'gpio' : gpios})
    data.loc[:,['gpio']] = data.gpio.apply(lambda x : "{0:b}".format(x))
    
    return data

#%%
parser = argparse.ArgumentParser(
                    prog='TaskLoadConfigurator',
                    description='Recorder and parser of intermittent devices power consumption and states, based on Nordic\'s nRF PPK2.')
                    
parser.add_argument("-f", "--file", help='If provided, use this file of pre-recorded data to extract the task list.', required=False)   
parser.add_argument("-v", "--voltage", type=int, help='Output voltage of PPK2 while recording in mV (Default = 3000 mV).', required=False, default = 3000)  
parser.add_argument("-t", "--time", type=int, help='Recording time in seconds (Default = 1s).',required=False, default=1)  

# GEt arguments from commandline
args = parser.parse_args()

if args.file:
    try:
        df = pd.read_csv("data_logger.csv", dtype = {'Timestamp(ms)': float, 'Current(uA)': float, 'D0-D7': str})
        print(">> Successfully loaded pre-recorded data from file.")
    except FileNotFoundError:
       raise(f"Error: Could not find/open {args.file}!")
    
    df = df.rename(columns={"Timestamp(ms)": "time", 'Current(uA)': "current_uA", "D0-D7": "gpio"})
else:
    print('=== WARNING: The recorder functionality seems to be missing samples. It is recommended to record in NRF Connect power profiler, export data as CSV from there and process CSV using this script. ===')
    # connect to the profiler
    if args.voltage > 5000 | args.voltage < 800:
        print("Invalid voltage (must be in in range 800-5000 mV)")
        
    print('>> Setup connection to power profiler.')
    profiler = power_profiler.PowerProfiler(None, args.voltage, None)

    #add 200ms just to make sure we have enough data, library throws away samples with stop measurement
    measurementTime = args.time + 0.2 

    # start the measurement
    print('>> Start recording.')
    profiler.start_measuring()
    profiler.enable_power()
    
    measurementStartTime = time.time()
    while(time.time() - measurementStartTime < measurementTime):
        time.sleep(0.1)
        
    profiler.stop_measuring()

    print('>> Recorded for ' + str(profiler.get_measurement_duration_s()) + ' seconds.')
    df = processInternalData(profiler.current_measurements)
    profiler.delete_power_profiler()
   
#%%
# Cut start-up
print(">> Processing data.")

startupCurrentThreshold = 50 # uA
df = df[df.index > df[df.current_uA > startupCurrentThreshold].index.min()].reset_index(drop=True)
df.loc[:, 'time'] = df.time - df.time.iloc[0]

# Set state until first GPIO change to zero (== startup time)
df.loc[df.time <= df[df['gpio'].astype(int).diff() != 0].time.iloc[1], 'gpio'] = 0
# Sanity check
if df.gpio.apply(lambda x: str(x).count("1") <= 1).all() == False:
  raise("Error: Multiple states active at the same time.")

df.loc[:, ['gpio_nr']] = df.gpio.apply(lambda x: str(x)[::-1].find("1")).values

# Get task changes
state_changes = df[df['gpio'].astype(int).diff() != 0].copy()
state_changes.loc[:,['length']] = abs(state_changes.time.diff(-1)).values
state_changes.loc[state_changes.index[-1], 'length'] = df.time.max() - state_changes.time.max()
state_changes.loc[:,['mean_current']] = state_changes.apply(lambda x : df[(df.time >= x.time) & (df.time < x.time + x.length)].current_uA.mean() * 1e-6, axis=1)

task_list = []
for state in state_changes.gpio_nr.unique():
    occurences = state_changes[state_changes.gpio_nr == state]
    task_name = task_names[str(state)] if str(state) in task_names else str(state)
    if state == -1:
        t = occurences.length.iloc[0]
        if len(occurences) > 1:
            print(f"Note: States without GPIO indicator measured! (T_mean = {occurences.length.iloc[1:].mean() * 1e-3}).")
    else:
        t = occurences.length.mean()
    i = occurences.mean_current.mean()

    task = {'name' : task_name,
            't' : t * 1e-3, #from ms to s
            'i' :  i}

    task_list.append(task)
           
print("== Extracted task list: ==")
pprint.pprint(task_list)
   

