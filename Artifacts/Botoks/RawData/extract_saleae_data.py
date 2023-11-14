# -*- coding: utf-8 -*-
"""
Load and extract data from traces (.sal files) recorded with Logic2 on saleae logic analyzer
and store as pandas dataframes (.pkl files).

Prerequisits: 
    - Install and open logic2 software from saleae
    - Tick 'Enable automation' in logic2 preferences
    - Install required python package: pip install logic2-automation

"""

import pandas as pd
import os
from saleae import automation

#We use absolute paths, because the saleae automation doesnt deal well with relative paths
basepath_measurements = '.'
json_path = './ExtractedData/DataLoadJson'

LOAD_ANALOG = False #Load also analog traces --> do only if really necessary and for single traces (files typically get huge!)

logic_manager =  automation.Manager.connect(port=10430)


#Load data of each measurement in folder
for file in filter(lambda x: x.endswith('.sal') and 'loop' in x, os.listdir(basepath_measurements)):
    
    #load saleae file and store it temporeally as .csv
    capture = logic_manager.load_capture(os.path.join(basepath_measurements, file))
    if LOAD_ANALOG:
        capture.export_raw_data_csv(directory=basepath_measurements, digital_channels=[0, 1, 2, 4], analog_channels=[ 2, 3])
    else:
        capture.export_raw_data_csv(directory=basepath_measurements, digital_channels=[0, 1, 2, 4]) 
        
    #get csv fil, process and store data as pandas dataframe (pickle)
    digital = pd.read_csv(os.path.join(basepath_measurements, 'digital.csv'))
    #digital = digital.rename({'Time [s]' : 'Time', 'Channel 0' : 'SENSE', 'Channel 1' : 'SEND', 'Channel 2' : 'V_OUT_DIG', 'Channel 4' : 'SEND_DONE'}, axis = 1) #for any other dataset
    digital = digital.rename({'Time [s]' : 'Time', 'Channel 0' : 'SENSE', 'Channel 1' : 'SEND', 'Channel 2' : 'V_OUT_DIG', 'Channel 4' : 'SEND_DONE'}, axis = 1) #for BQ dataset
    digital.to_pickle(os.path.join(json_path, file.strip('.sal') + '_digital.pkl'))
    
    if LOAD_ANALOG:
        analog = pd.read_csv(os.path.join(basepath_measurements, 'analog.csv'))
        analog = analog.rename({'Time [s]' : 'Time', 'Channel 2' : 'V_OUT', 'Channel 3' : 'V_CAP'}, axis = 1)
        analog.to_pickle(os.path.join(json_path, file.strip('.sal') + '_analog.pkl'))
    