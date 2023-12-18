# -*- coding: utf-8 -*-
"""
SIMBA Simulation core
"""

import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
import datetime
import numpy as np
import importlib
VERBOSE = False

#%%
def cap_factory(config, time_base):
    cls = getattr(importlib.import_module(f'Capacitors.{config["type"]}'), config['type'])
    return cls(config['settings'], VERBOSE, time_base)

def converter_factory(config, time_base):
     cls = getattr(importlib.import_module(f'Converters.{config["type"]}'), config['type'])
     return cls(config['settings'], VERBOSE, time_base)

def harvester_factory(config, time_base):
     cls = getattr(importlib.import_module(f'Harvesters.{config["type"]}'), config['type'])
     return cls(config['settings'], VERBOSE, time_base)
 
def load_factory(config, time_base):
     cls = getattr(importlib.import_module(f'Loads.{config["type"]}'), config['type'])
     return cls(config['settings'], VERBOSE, time_base)

class Simulation:

    def __init__(self, cap_config, harvester_config, converter_config, load_config, log_keys = [], log_triggers = []):
        
        self.min_step_size = 1e-6 #us as timing base
        self.max_step_size = 1e-3 #at least every xxx s
        
        self.cap = cap_factory(cap_config, self.min_step_size)
        self.load = load_factory(load_config, self.min_step_size)
        self.harvester = harvester_factory(harvester_config, self.min_step_size)
        self.converter = converter_factory(converter_config, self.min_step_size)
        
        self.log_keys = log_keys
        self.log_trigger = log_triggers
        self.force_log = log_keys != [] and log_triggers == []
                
    def reset(self, time_end):
        self.sim_end = int(time_end / self.min_step_size)
        self.max_step = int(self.max_step_size / self.min_step_size)
        
        self.cap.reset() 
        self.converter.reset(self.cap.voltage, self.harvester.get_ocv(0))
        self.load.reset(self.converter.get_output_operating_voltage(self.cap.voltage), self.cap.voltage)
        harvester_ocv = self.harvester.get_ocv(0)
        self.harvester.reset(self.converter.get_input_operating_voltage(self.cap.voltage, harvester_ocv, 0))
        
        self.log = []
        self.log_processed = False
        
        self.load_event = 0
        self.cap_event = 0
                                
    def run(self, until = 10):
        self.reset(until)
        assert until <= self.harvester.time_max * self.min_step_size, "Cannot start simulation: Simulation time exceeds harvesting trace."
        self.execute()

    def execute(self):   
        self.time = 0
        start = datetime.datetime.now()
        while self.time < self.sim_end:
            
            # Store certain variables locally for logging 
            self.v_cap = self.cap.voltage
            self.state = self.load.get_state()
            
            # Get incoming power at current point in time, depends on voltage, harvester and converter
            self.harvester_ocv = self.harvester.get_ocv(self.time)
            self.v_in = self.converter.get_input_operating_voltage(self.v_cap, self.harvester_ocv, self.time) 
            self.i_in = self.harvester.get_current(self.time, self.v_in) 
            self.efficiency_in = self.converter.get_input_efficiency(self.v_in, self.i_in)
     
            # Get outgoing power at current point in time, depends on voltage, converter and load
            self.v_out = self.converter.get_output_operating_voltage(self.v_cap)
            self.i_out = self.load.get_current(self.v_out)
            self.efficiency_out =  self.converter.get_output_efficiency(self.v_cap, self.i_out)
            
            # Quiescent currents within the system 
            self.i_leak_converter = self.converter.get_quiescent(self.cap.voltage)
            
            v_in_adjust = (self.v_in / self.v_cap) if self.v_cap > 0 else 1
            v_out_adjust = (self.v_out / self.v_cap) if (self.v_cap > 0) else 1
            self.i_total = self.i_in * v_in_adjust * self.efficiency_in - self.i_out * v_out_adjust / self.efficiency_out - self.i_leak_converter   
 
            # Compute when we have to update our simulation the next time
            self.dt = self.compute_next_update(self.i_total)
            next_time = self.dt + self.time
   
            self.log_data(self.time, self.force_log)
            #print(f"{self.time} : dt = {self.dt}; i_in = {self.i_in}, i_out = {self.i_out}, i_total = {self.i_total}, vcap = {self.cap.voltage}, state = {self.load.state.name}")
             
            # update and log
            self.harvester.update_state(next_time, self.dt, self.v_in) 
            self.cap.update_state(self.time, self.dt, self.i_total) 
            self.converter.update_state(next_time, self.dt, self.cap.voltage) #might be necessary for bq255xx etc.
            if self.load.update_state(next_time, self.dt, self.converter.get_output_operating_voltage(self.cap.voltage), self.cap.voltage) == 'FORCE_OFF':
                self.converter.turn_off(self.cap.voltage) #if load asks for a 'self-shutoff', the converter has to serve this
                
            self.time = next_time       
                
        if VERBOSE:
            print(f"Total elapsed time for simulation: {datetime.datetime.now() - start}.")
            
        # Log last state as well    
        self.log_data(self.time, True)
        self.load.process_log(self.time)
        self.cap.process_log(self.time)
        self.harvester.process_log(self.time)
       
        
    #compute time until next update is necessary (i.e., the maximum timestep until the next state change happens in any of the modules)
    def compute_next_update(self, i):
                 
        #Get next update times from all the system's components
        t_in_update = self.harvester.get_next_change(self.time)
        t_load_update = self.load.get_next_change(self.time)
        t_cap_update = self.cap.get_next_change(i, self.load.voltage_monitor.get_next_threshold(self.cap.voltage, i)) #tell us when we reach the next voltage threshold
        t_converter_update = self.cap.get_next_change(i, self.converter.voltage_monitor.get_next_threshold(self.cap.voltage, i)) #TODO: get also information, when there will be an update in the converter
        
        self.updates = [t_in_update, t_load_update, t_cap_update, t_converter_update]        
        
        t = min((x for x in self.updates if x is not None), default = self.max_step)
        return min(self.max_step, t) # we make a simulation step at least every max_step_size
     
    def log_data(self, time, force_log):

        if (len(self.log) == 0) or force_log \
           or any(self.log[-1][trig] != getattr(self, trig) for trig in self.log_trigger):
           # or (time / self.min_step_size == self.sim_end - 1):
            #self.log.loc[time, :] = [cap_voltage, load_state, i_in, v_in, p_in, i_load, v_load, p_out, p_leak_cap, p_leak_converter]
            log_dict = {}
            for key in self.log_keys:
                log_dict[key] = getattr(self, key)
            log_dict['time'] = (time * self.min_step_size)
            self.log.append(log_dict.copy())
            
    def process_log_data(self, keep_only_state_changes = False): 
    
        #self.log_old = self.log #debugging simulation  
        self.log = pd.DataFrame(self.log)
               
        # Keep only first columns and columns, where the state has changed
        # if keep_only_state_changes:
        #     start = self.log.iloc[0]
        #     self.log = pd.concat([start.to_frame().T, self.log[self.log.state.ne(self.log.state.shift().bfill())].copy()]) 
        #     self.log.reset_index(inplace = True, drop=True)
        
        #store time interval of each state and remove data after last RESTORE state (to ensure fair forward progress comparison)
        self.log['Interval'] = self.log.time.diff().shift(-1)
        if self.log.time.iloc[-1] == self.log.time.iloc[-2]:
            self.log = self.log.drop(self.log.tail(1).index)
        
        #self.log = self.log[self.log.index <= self.log[self.log.State == LoadState.RESTORE].index.max()].copy() #copy to avoid python warnings
        
        self.log_processed = True
            
    def plot_sim_result(self, title = ""):
        
        if not self.log_processed:
             self.process_log_data()
             
        if len(self.log) == 0:
            print("No data to plot!")
            return
            
        fig, axs = plt.subplots(nrows=2, sharex=True)
        
        #Plot voltage and currents over time
        self.log.plot(x='time', y='cap_voltage', ax=axs[0], color='black')
        self.log.plot(drawstyle = 'steps-pre', x='time', y=['i_in', 'i_load', 'i_total'], ax=axs[1], color = ['black', 'grey', 'white'])

        #Overlay colors for load states
        # Keep only first columns and columns, where the state has changed for plotting the colors
        start = self.log.iloc[0]
        last = self.log.iloc[-1]
        state_changes = pd.concat([start.to_frame().T, self.log[self.log.state.ne(self.log.state.shift().bfill())].copy(), last.to_frame().T]) 
        state_changes.reset_index(inplace = True)

        for ax in axs:
            y0, y1 = ax.get_ylim()
            for idx, row in state_changes.iloc[:-1].iterrows():
                ax.fill_between([row.time, state_changes.iloc[idx + 1].time], y0, y1, color = self.load.color_map[row.state], alpha=0.2)
        #Legend for state colors
        legend_elements = []
        for state in state_changes.state.unique():
            legend_elements.append(Patch(facecolor=self.load.color_map[state], edgecolor=self.load.color_map[state], label=state, alpha=0.2))
           
        fig.legend(handles=legend_elements, loc='lower center', ncol = len(legend_elements))
        fig.suptitle(title)
       
    
    def get_sim_log(self):
        
        if not self.log_processed:
            self.process_log_data()

        return self.log
    
    
"""
Trade-off exploration tool
"""

import multiprocessing as mp
from itertools import product
import datetime
import pickle
import os
import pandas as pd
import time
import pathlib
import json

def save_log_to_file(log_path, sim_num, parameter_settings, sim_instance):
    
        path = pathlib.Path(log_path)
        path.mkdir(parents=True, exist_ok=True)
        
        try:
            file_path = os.path.join(path, f"log_sim{sim_num}.pkl")
            file = open(file_path, 'wb')
        except Exception as FileNotFoundError:
            print(f"Error could find file: {file_path}")     
            
        #store parameter settings in first line
        #file.write(json.dumps(parameter_settings))
        pickle.dump(parameter_settings, file)
        
        #store log for each module in seperate line
        for mod in ['cap', 'load', 'harvester', 'converter']:        
            #file.write("\n")              
            log = getattr(sim_instance, mod).get_log()
            pickle.dump(log, file)
            
        file.close()
                    
def load_log_from_file(log_file_path):
    try:
        with open(log_file_path, 'r') as file:
            param_settings = json.loads(file.readline())
            
            cap_log = pd.read_json(file.readline(), orient='split')
            load_log = pd.read_json(file.readline(), orient='split')
            harvester_log = pd.read_json(file.readline(), orient='split')
            converter_log = pd.read_json(file.readline(), orient='split')         
        
    except FileNotFoundError:
        print(f"Error could find file: {log_file_path}")
        
    return param_settings, cap_log, load_log, harvester_log, converter_log

def load_log_from_file_pkl(log_file_path):
    try:
        with open(log_file_path, 'rb') as file:
            param_settings = pickle.load(file)
            
            cap_log = pd.read_pickle(file)
            load_log = pd.read_pickle(file)
            harvester_log = pd.read_pickle(file)
            converter_log = pd.read_pickle(file)         
        
    except FileNotFoundError:
        print(f"Error could find file: {log_file_path}")
        
    return param_settings, cap_log, load_log, harvester_log, converter_log
        
    


def run_experiment(num, params_to_change, base_config, metrics, settings, mapping_params):
    
    #print("Start simulation with:")
    #print(params_to_change)
    
    # Store simulation settings
    timestep = settings['timestep'] if 'timestep' in settings else 1e-3
    store_log_data = settings['store_log_data'] if 'store_log_data' in settings else False
    store_log_path = settings['log_path'] if 'log_path' in settings else '.'
    normalize_stats = settings['normalize_stats'] if 'normalize_stats' in settings else False
    
    #print(f"Timestep: {timestep}.")
    #print(f"Store log data: {store_log_data} (@ {store_log_path}).")
    
    # Create simulation core with base configuration
    sim = Simulation(base_config['capacitor'], base_config['harvester'], base_config['converter'], base_config['load'])
    sim.max_step_size = timestep
    
    result = {}
    # Adjust parameters in modules accordingly
    for param_to_change in params_to_change:
        try:
            module_to_change = getattr(sim, param_to_change['module'])
        except AttributeError:
            print("Cannot change module parameter, as module does not exist! (Use 'cap', 'harvester', 'converter', or 'load'!)")
            return -1 #TODO Error handling?
        
        if hasattr(module_to_change, param_to_change['param']):
            setattr(module_to_change, param_to_change['param'], param_to_change['value'])
        else:
            print(f"Cannot change module parameter {param_to_change['module']}.{param_to_change['param']}, as parameter does not exist!")
            return -1 #TODO Error handling
        
        #add parameter settings to result for later analysis
        result[f"{param_to_change['module']}.{param_to_change['param']}"] = param_to_change['value']
    
    # Set parameters that are mapped to certain settings if applicable
    for mapping_param in mapping_params:
        module_to_map = getattr(sim, mapping_param['module_to_map'])
        
        if hasattr(module_to_map, mapping_param['param_to_map']):
            map_value = getattr(module_to_map, mapping_param['param_to_map'])
            map_value = mapping_param['mapping'][map_value]
        else:
            print(f"Cannot retrieve mapping parameter {mapping_param['module_to_map']}.{mapping_param['param_to_map']} while mapping, as parameter does not exist!")
            return -1 #TODO Error handling
        
        module_to_change = getattr(sim, mapping_param['module_to_change'])
        if hasattr(module_to_change, mapping_param['param_to_change']):
            setattr(module_to_change, mapping_param['param_to_change'], map_value)
        else:
            print(f"Cannot change module parameter {mapping_param['module_to_change']}.{mapping_param['param_to_change']} while mapping, as parameter does not exist!")
            return -1 #TODO Error handling
    
    # Run simulation
    try:
        sim.run(base_config['sim_time'])
    except Exception as e:
        print("Expection during simulation!!!")
        print(e)
        
    #print("Simulation done.")
                   
    # Extract requested metrics from simulator's modules
    try: 
        for module_metrics in metrics:
            try:
                module = getattr(sim, module_metrics['module'])
            except AttributeError:
                print("Cannot retrieve module metrics, as module does not exist! (Use 'cap', 'harvester', 'converter', or 'load'!)")
                return -1 #TODO Error handling?
            
            stats = module.get_log_stats(normalize_stats)
            for metric in module_metrics['params']:
                try:
                    result[f"{module_metrics['module']}.{metric}"] = stats[metric]
                except KeyError:
                    result[f"{module_metrics['module']}.{metric}"] = None
    except Exception as e:
        print(e)
       
    # Store detailed log of simulation to file if requested
    if store_log_data:
        save_log_to_file(store_log_path, num, result, sim)
            
    return result

    
def run_tradeoff_exploration(params, metrics, base_config, settings = {}, mapping_params = []):
    result_list = []
    process_results = []
    
    def log_result(result):
        # This is called whenever foo_pool(i) returns a result.
        # result_list is modified only by the main process, not the pool workers.
        result_list.append(result)
    
    # Decode given parameters to explore accordingly
    parameter_options = list(product(*params.values())) #Permutate all provided parameters
    module_list = [key.split(".")[0] for key in params.keys()]
    param_list = [key.split(".")[1] for key in params.keys()]

    param_options = []
    for parameters in parameter_options:
        params_to_change = [{'module' : module_list[i], 'param' : param_list[i], 'value' : val} for i, val in enumerate(parameters)]
        param_options.append(params_to_change)
    
    # Since we have all paramter options, we can now start a simulation for each option
    start = datetime.datetime.now()
    pool = mp.Pool(min(int(mp.cpu_count()/2), len(param_options)))
    print(f"Create {min(int(mp.cpu_count()/2), len(param_options))} processes.")
    
    # Each simulation runs in a seperate process and concurrently
    for num, params_to_change in enumerate(param_options):
        process_result = pool.apply_async(run_experiment, args = (num, params_to_change, base_config, metrics, settings, mapping_params), callback=log_result)
        process_results.append(process_result)
    # Close Pool and let all the processes complete    
    pool.close()
    pool.join()  # postpones the execution of next line of code until all processes in the queue are done.
    
    while True:
        time.sleep(1)
        # catch exception if results are not ready yet
        try:
            ready = [result.ready() for result in process_results]
            successful = [result.successful() for result in process_results]
        except Exception:
            continue
        # exit loop if all tasks returned success
        if all(successful):
            break
        # raise exception reporting exceptions received from workers
        if all(ready) and not all(successful):
            raise Exception(f'Workers raised following exceptions {[result._value for result in process_results if not result.successful()]}')
    
    print(f"Total time : {datetime.datetime.now() - start}")
    return result_list