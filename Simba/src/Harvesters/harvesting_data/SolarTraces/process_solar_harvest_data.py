# -*- coding: utf-8 -*-
"""
Created on Wed Jan 25 09:33:50 2023

@author: hannib
"""

folder_source = 'NREL' #folder including 'raw data' (from datasets)
folder_dest = '.'      #folder where processed data should be stored

data_set = 'NREL'      #type of data; currently supported: NREL, ENHANTS 

import pandas as pd
import os
import datetime
import json

from pathlib import Path
        
enhants_columns = {'sec'  : int,
                    'irr,microW/cm^2' : float,
                    'year' : int,
                    'mon'  : int,
                    'day'  : int,
                    'hh'   : int,
                    'mm'   : int,
                    'ss'   : int}

for file in os.listdir(folder_source):
    
    if data_set == 'ENHANTS':
   
        df = pd.read_csv(os.path.join(folder_source, file), dtype=enhants_columns, delimiter='\t', skipinitialspace=True)
         
        start_time = datetime.datetime(year = df.year.iloc[0], month = df.mon.iloc[0], 
                                       day = df.day.iloc[0], hour=df.hh.iloc[0], minute=df.mm.iloc[0], second=df.ss.iloc[0])
        
        #Process data and get rid of incorrect data
        df = df[['sec', 'irr,microW/cm^2', 'ss', 'hh', 'mm']] #we are only interested in total time in sec and irradiance
        df = df.rename({'irr,microW/cm^2' : 'irradiance'}, axis=1)
        #keep only days which don't have any corrupt data
        df['day_nr'] = df['sec'].apply(lambda x : int(x/(60*60*24)))
        corrupt_days = df[df.irradiance.isnull()].day_nr.unique()
        
        df['day_sec'] = df['sec'].apply(lambda x : x % (60*60*24))
        df = df[~df.day_nr.isin(corrupt_days)]
        for cnt, day_nr in enumerate(df.day_nr.unique()):
            df.loc[df.day_nr == day_nr,'day_nr'] = cnt
        
        #update seconds to have a trace without gaps
        df['sec_new'] = df.day_sec  + df.day_nr*24*60*60
        df['sec_new'] = df.sec_new - df.sec_new.iloc[0] #start at t = 0
        df = df[['irradiance', 'sec_new', 'day_nr']] #drop the rest
        
        df = df.set_index('sec_new')
        df['irradiance'] /= 1e2 #to W/m
            
        
    elif data_set == 'NREL':
        
        df = pd.read_csv(os.path.join(folder_source, file), delimiter=',', names=['day', 'time', 'irradiance'], parse_dates={'timestamp':['day', 'time']}, infer_datetime_format=True)
        df['irradiance'] = df.irradiance.apply(lambda x : 0 if x < 0 else x)
        df['sec'] = df.timestamp.apply(lambda x : int((x - df.timestamp.iloc[0]).total_seconds()))
        df['day_nr'] = df['sec'].apply(lambda x : int(x/(60*60*24)))
        
        start_time = df.timestamp.iloc[0]
        
        df = df.drop("timestamp", axis = 1)
        df = df.set_index('sec')
    
    #only keep data where irradiance has changed
    start = df.iloc[0]
    df = pd.concat([start.to_frame().T, df[df.irradiance.ne(df.irradiance.shift().bfill())].copy()])
        
    info = {'Type' : data_set,
            'StartTime' : str(start_time),
            'Season' : 0, #todo
            'TraceLength' : int(df.index.max())}
    
    with open(os.path.join(folder_dest, Path(file).stem + '.json'), 'w') as f:
        f.write(json.dumps(info))
        f.write("\n")
        df.to_json(f)  
    
        
