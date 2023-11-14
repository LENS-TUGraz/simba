# -*- coding: utf-8 -*-
"""
Load module implementation:

TaskLoad

TODO: description
"""

from aenum import Enum, extend_enum
import pandas as pd
from VoltageMonitor import VoltageMonitor
                   
class TaskLoad:
    
    States = Enum("State", ['OFF'])
    Events = Enum("Events", ['NONE', 'ON', 'OFF'])
    
    def __init__(self, config, verbose, time_base):
        self.verbose = verbose
        if verbose:
            print("Create Task load.")
            
        self.time_base = time_base
            
        self.log_full = config['log'] if 'log' in config else True
        self.verbose_log = config['verbose_log'] if 'verbose_log' in config else False

        self.v_on = config['v_on']
        self.v_off = config['v_off']
        thresholds = [("ON", config['v_on'], "rising"),
                      ("OFF", config['v_off'], "falling")]
        self.voltage_monitor = VoltageMonitor(thresholds)
                
        self.register_tasks(config['tasks'])
        self.start_task = config['skip_initial_task'] if 'skip_initial_task' in config else 0
        self.i_off = config['i_off']
        self.shutdown_after_completion = config['shutdown_after_completion'] if 'shutdown_after_completion' in config else False
                      
    def register_tasks(self, tasks):
        self.tasks = tasks
        self.num_tasks = len(self.tasks)
        
        #register each task as load state
        for t in tasks:
            try:
                extend_enum(self.States, t['name'])
            except: #to avoid warning when reexuting pyhton module
                pass
            
            try:
                extend_enum(self.Events, f"{t['name']}_DONE")
            except: #to avoid warning when reexuting pyhton module
                pass
    
    def reset(self, initial_voltage, initial_cap_voltage):
        self.state = self.States.OFF if initial_voltage <= self.v_off else self.States(2) #State 2 = first user task
        self.old_voltage = initial_voltage
        self.current_task = 0 #we start with first task
        
        self.voltage_monitor.reset()
        if self.state == self.States.OFF:
            self.voltage_monitor.unregister_event('OFF')
            self.next_update = (self.Events.NONE, None)
        else:
            self.voltage_monitor.unregister_event('ON')
            self.next_update = (self.Events[f'{self.state.name}_DONE'], int(self.tasks[self.current_task]['t'] / self.time_base))
        
        self.log_processed = False
        self.log = [{'time' : 0, 
                     'event' : self.Events.NONE.name, 
                     'i_out' : self.get_current(initial_voltage), 
                     'state' : self.state.name,
                     'v_out' : initial_voltage,
                     'v_cap' : initial_cap_voltage,
                     'task_success' : False}]
        
        #Init dict for statistics
        self.stats = {}
        for stat in ['time', 'time_wasted', 'energy', 'energy_wasted', 'num_success', 'num_fail']:
            for state in self.States:
                self.stats[f'{stat}_{state.name}'] = 0
        
        self.start_time_state = 0
        self.start_energy_state = 0
        
    def get_state(self):
        return self.state
    
    def set_state(self, state):
        self.state = state
        
    def get_current(self, voltage): #no voltage dependency so far
        assert ((self.state != self.States.OFF) and (voltage > self.v_off)) \
            or ((self.state == self.States.OFF) and (voltage < self.v_on)) \
            or (self.shutdown_after_completion == True),\
            "Error: Load in wrong state, cannot be turned on/off with this voltage level"
        
        if self.state == self.States.OFF:  # if we are on, the appl. gives the current consumption
            return self.i_off
        else:
            return self.tasks[self.current_task]['i']

    def get_next_change(self, time): #
        return None if self.next_update[1] == None else self.next_update[1] - time
                
    def update_state(self, time, dt, input_voltage, cap_voltage):
        
        assert (self.next_update[1] == None) or (time <= self.next_update[1]), "Error: Missed a load update."
        
        self.sim_event = None
        
        self.stats[f'time_{self.state.name}'] += dt * self.time_base
        self.stats[f'energy_{self.state.name}'] += self.old_voltage * self.get_current(self.old_voltage) * dt * self.time_base
        
        voltage_event = self.voltage_monitor.get_event(self.old_voltage, input_voltage)
        load_event = self.next_update[0] if self.next_update[1] != None and (self.next_update[1] == time)  else None
        self.old_voltage = input_voltage
        
        if (voltage_event == None and load_event == None):
            if self.verbose_log:
                self.log.append({'time' :  time * self.time_base, 
                                  'event' : self.Events.NONE.name, 
                                  'i_out' : self.get_current(input_voltage), 
                                  'state' : self.state.name, 
                                  'v_out' : input_voltage,
                                  'v_cap' : cap_voltage,
                                  'task_success' : False})
            return self.sim_event #nothing to do
        
        #Update load's state machine
        if voltage_event == self.voltage_monitor.Events.OFF: #todo: account for hysteresis in voltage manager
            load_event = self.turn_off(time, load_event)
            
        elif voltage_event == self.voltage_monitor.Events.ON:
            load_event = self.turn_on(time, load_event)
            
        elif load_event != None:
            load_event = self.schedule_next_task(time, load_event)
            
        else:
            assert False, "Error in implementation." 
                            
        self.start_time_state = time
        self.start_energy_state = self.stats[f'energy_{self.state.name}']
            
        if self.log_full:        
            if load_event != self.Events.NONE:
                self.log.append({'time' : time * self.time_base, 
                                  'event' : load_event.name, 
                                  'i_out' : self.get_current(input_voltage), 
                                  'state' : self.state.name, 
                                  'v_out' : input_voltage,     
                                  'v_cap' : cap_voltage,
                                  'task_success' : self.task_success})
        return self.sim_event
     
        
    def turn_on(self, time, load_event):
        
        assert self.state == self.States.OFF, "Error: Error in state machine (should be turned off)."
        assert load_event == None, "Error in state machine. In OFF mode the load is not expecting an event."
        
        #Log number of off states for completeness
        self.stats[f'num_success_{self.state.name}']
        
        self.voltage_monitor.unregister_event('ON')
        self.voltage_monitor.register_event('OFF', self.v_off, 'falling')
               
        # After turning on, we start with initial task        
        self.current_task = 0
        self.task_success = False
        self.state = self.States[self.tasks[self.current_task]['name']]
        self.next_update = (self.Events[f'{self.state.name}_DONE'], time + int(self.tasks[self.current_task]['t']/self.time_base))
        
        return self.Events.ON
        
    def turn_off(self, time, load_event):
        
        assert self.state != self.States.OFF, "Error: Error in state machine (should be turned on)."
        
        if load_event == None: #we didn't finish the previous task; just log the fail
            self.stats[f'num_fail_{self.state.name}'] += 1
            self.stats[f'time_wasted_{self.state.name}'] += (time - self.start_time_state) * self.time_base
            self.stats[f'energy_wasted_{self.state.name}'] += self.stats[f'energy_{self.state.name}'] - self.start_energy_state
            self.task_success = False
            event = self.Events.OFF
        else:
            self.stats[f'num_success_{self.state.name}'] += 1
            self.task_success = True
            event = self.Events[f'{self.state.name}_DONE']
            
        self.state = self.States.OFF    
        self.next_update = (self.Events.NONE, None)
        self.voltage_monitor.unregister_event('OFF')
        self.voltage_monitor.register_event('ON', self.v_on, 'rising') 
        
        return event
    
    def schedule_next_task(self, time, load_event):
        assert self.state != self.States.OFF, "Error: Error in state machine (should not receive such an event in OFF state)."
        assert load_event != self.Events.NONE, "Something went wrong."
               
                
        if (self.current_task == self.num_tasks - 1) and self.shutdown_after_completion:
            load_event = self.turn_off(time, load_event)
            self.sim_event = 'FORCE_OFF'
            self.old_voltage = 0 #small hack?
        else:
            
            #If we are here, we successfully finished the last task
            self.task_success = True #stor for logs
            self.stats[f'num_success_{self.state.name}'] += 1
               
            if self.current_task < self.num_tasks - 1:
                self.current_task = self.current_task + 1
            else:
                self.current_task = self.start_task   #skip first (initial) task
                
            self.state = self.States[self.tasks[self.current_task]['name']]
            self.next_update = (self.Events[f'{self.state.name}_DONE'], time + int(self.tasks[self.current_task]['t'] / self.time_base)) 

        return load_event
        
    def process_log(self, time_max):        
        self.log = pd.DataFrame(self.log)
        self.log.loc[:, 'dt'] = abs(self.log.time.diff(-1))
        self.log.loc[self.log.index[-1],'dt'] = time_max * self.time_base - self.log.time.iloc[-1]
        self.log.loc[:,'p_out'] = self.log.i_out * (self.log.v_out.shift(-1) + self.log.v_out)/2 #interpolate/estimate power consumption between two different voltage points
        self.log_processed = True
        
    
    def get_log(self):  
        if not self.log_processed:
            self.process_log()
    
        return self.log
    
    def get_log_stats(self, normalize = True):

        load_log = self.log[self.log.event != 'NONE'].reset_index().copy()
        
        #Filter to make results comparable
        if normalize:
            try:
                start_idx = load_log[load_log.state == 'OFF'].index[0]
                end_idx = load_log[load_log.state == 'OFF'].index[-1] - 1
                load_log = load_log.iloc[start_idx : end_idx].copy()
            except:
                pass
        
        if not load_log.empty:      
            #update dt and p_out accordingly
            last_time = load_log.iloc[-1]['time'] #we need to store the last dt
            load_log.loc[:,'dt'] = abs(load_log.time.diff(-1))   
            load_log.loc[load_log.index[-1], 'dt'] = last_time - load_log.iloc[-1].time
            load_log.loc[:,'p_out'] = load_log.i_out * (load_log.v_out.shift(-1) + load_log.v_out)/2 #interpolate/estimate power consumption between two different voltage points
            load_log.loc[load_log.index[-1],'p_out'] = load_log.iloc[-1].i_out * load_log.iloc[-1].v_out
            
            #Get mean/max time of OFF state
            self.stats['time_off_mean'] = load_log[load_log.state == 'OFF'].dt.mean()
            self.stats['time_off_max'] = load_log[load_log.state == 'OFF'].dt.max()
            
            #Get mean/max time when load is turned off -- this might never happen
            try:
                self.stats['time_cycle_mean'] = load_log[load_log.event == 'ON'].time.diff().mean()
            except:
                self.stats['time_on_mean'] = 0
                
            #Get mean/max time between each task
            for task in self.tasks:
                try:
                    self.stats[f'time_between_{task["name"]}_mean'] = load_log[load_log.event == f'{task["name"]}_DONE'].time.diff().mean()
                    self.stats[f'time_between_{task["name"]}_max'] = load_log[load_log.event == f'{task["name"]}_DONE'].time.diff().max() 
                except:
                    self.stats[f'time_between_{task["name"]}_mean'] = 0
                    self.stats[f'time_between_{task["name"]}_max'] = 0

        else:
            self.stats['time_on_mean'] = 0
            self.stats['time_off_mean'] = 0
            self.stats['time_off_max'] = 0
            for task in self.tasks:
                self.stats[f'time_between_{task["name"]}_mean'] = 0
                self.stats[f'time_between_{task["name"]}_max'] = 0
            

        return self.stats