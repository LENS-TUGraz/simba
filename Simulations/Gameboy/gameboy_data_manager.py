# -*- coding: utf-8 -*-
"""
Helper functions to load/extract experimental data of Gameboy experiments
"""

import pandas as pd
import os
import matplotlib.pyplot as plt

def load_gameboy_trace_digital(path, file, time_max = None):
    
    data_measured_dig = pd.read_pickle(os.path.join(path, file + '_digital.pkl'))      
        
    if time_max != None:
        data_measured_dig = data_measured_dig[data_measured_dig.Time <= time_max].copy()
        
    return data_measured_dig

def get_gameboy_stats(data_measured_dig):
        
    #Keep only columns, where the output (voltage) state changes and compute length of these states
    data_measured_vout = data_measured_dig[data_measured_dig.V_OUT_DIG.diff() != 0].reset_index()[['Time', 'V_OUT_DIG']]
    data_measured_vout = data_measured_vout.iloc[1:-1] #skip first and last state (might be cutted off)
    data_measured_vout['TimeDiff'] = abs(data_measured_vout.Time.diff(-1))
    
    
    data_measured_send_done = data_measured_dig[data_measured_dig.SEND_DONE.diff() != 0].reset_index()[['Time', 'SEND_DONE']]
    data_measured_send_done['TimeDiff'] = abs(data_measured_send_done[data_measured_send_done == 1].Time.diff(-1))
    
    stats = {}
    
    #Extract statistics
    try:
        stats['TotalTimeOn'] = data_measured_vout.groupby('V_OUT_DIG').sum()['TimeDiff'][1]
        stats['MeanTimeOn'] = data_measured_vout.groupby('V_OUT_DIG').mean()['TimeDiff'][1]
        stats['MeanTimeOff'] = data_measured_vout.groupby('V_OUT_DIG').mean()['TimeDiff'][0]
        stats['TotalTimeOff'] = data_measured_vout.groupby('V_OUT_DIG').sum()['TimeDiff'][0]
    except KeyError: #if current is high enough, there are no off times
        stats['MeanTimeOff'] = 0
        stats['TotalTimeOff'] = 0 
        stats['MeanTimeOn'] = 0
        stats['TotalTimeOn'] = 0
        
    try:
        stats['MeanTimeSample'] = data_measured_send_done[data_measured_send_done.SEND_DONE == 1].Time.diff().mean()
        stats['MaxTimeSample'] = data_measured_send_done[data_measured_send_done.SEND_DONE == 1].Time.diff().max()
        stats['NumSamples'] = data_measured_send_done[data_measured_send_done.SEND_DONE == 1].SEND_DONE.sum()
    except KeyError: #if current is too low or cap is too low
        stats['MeanTimeSample'] = 0 
        stats['MaxTimeSample'] = 0 
        stats['NumSamples'] = 0
        
    return stats



def load_gameboy_trace_analog(path, file, time_max = None):
    data_measured_ana = pd.read_pickle(os.path.join(path,file + '_analog.pkl'))
    
    if time_max != None:
        data_measured_ana = data_measured_ana[data_measured_ana.Time <= time_max].copy()
    
    
    return data_measured_ana

def plot_gameboy_trace(dig_data, analog_data = None, axs = []):
    if len(axs) == 0:
        fig, axs = plt.subplots(nrows = 2, sharex=True)
    
    dig_data['RESTORE'] = dig_data['RESTORE']*0.8 + 2
    dig_data['CHECKPOINT'] = dig_data['CHECKPOINT']*0.8 +1
    dig_data['CHECKPOINT_DONE'] = dig_data['CHECKPOINT_DONE']*0.8 
    
    dig_data.plot(x='Time', y=['RESTORE', 'CHECKPOINT', 'CHECKPOINT_DONE'], ax=axs[0], drawstyle='steps-post', legend=False)
    axs[0].set_yticks([0, 1, 2])
    axs[0].set_yticklabels(['CHKPT_OK', 'CHKPT', 'RESTORE'])
    analog_data.plot(x='Time', y='VBAT', label='$V_{cap}$', color='black', linestyle='dashed', ax=axs[1])
    analog_data.plot(x='Time', y='VOUT', label='$V_L$', color='grey', linestyle='solid', ax=axs[1], ylabel="Voltage (V)")
    analog_data.plot(x='Time', y='VIN', label='$V_H$', color='lightgrey', linestyle='solid', ax=axs[1], ylabel="Voltage (V)") 