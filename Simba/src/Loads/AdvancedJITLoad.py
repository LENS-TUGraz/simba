# -*- coding: utf-8 -*-
"""
Load module implementation:

AdvancedJITLoad

TODO: description
"""

from aenum import Enum
import pandas as pd
from VoltageMonitor import VoltageMonitor
                   
class AdvancedJITLoad:
    
    States = Enum("State", ['OFF', 'ON', 'RESTORE', 'SAVE', 'SLEEP'])
    Events = Enum("Events", ['NONE', 'SAVE_START', 'RESTORE_START', 'SAVE_SUCCESS', 'RESTORE_SUCCESS', 'SAVE_FAIL', 'RESTORE_FAIL', 'APPLICATION_EVENT', 'FORCED_OFF'])
    color_map = {'ON' : 'green',
                 'SAVE' : 'blue',
                 'RESTORE' : 'lightblue',
                 'OFF' : 'red'}
    state = States.ON #todo: initial state from settings
    
    def __init__(self, config, verbose, time_base):
        
        self.verbose = verbose
        if verbose:
            print("Create JIT load.")
            
        self.time_base = time_base
        self.log_full = config['log'] if 'log' in config else True
            
        thresholds = [("RESTORE", config['v_restore'], "rising"),
                      ("SAVE", config['v_save'], "falling"),
                      ("OFF", config['v_min'], "falling")] #todo: make it work that both rising and falling edge of this voltage trigger a simulation round
        self.voltage_monitor = VoltageMonitor(thresholds)
        self.v_min = config['v_min']
                
        self.currents = dict()
        for state in self.States:
              self.currents[state] = config['currents'][state.name] if state.name in config['currents'] else 0
              
        self.t_restore = config['t_restore'] 
        self.t_save = config['t_save'] 
        
        self.initial_state = config['initial_state'] if 'initial_state' in config else 'OFF'
        
        #create scheduler
        cls = getattr(AdvancedJITLoad, config['application']['type'])
        self.application = cls(config['application'], verbose, self.time_base)

                          
    def reset(self, initial_voltage, initial_cap_voltage):
        self.state = self.States[self.initial_state] 
        self.old_board_voltage = initial_voltage
        self.old_cap_voltage = initial_cap_voltage
        
        self.voltage_monitor.reset()
        self.application.reset()
        
        self.t_restore_s = int(self.t_restore / self.time_base)
        self.t_save_s = int(self.t_save / self.time_base)
        
        if self.state == self.States.ON:
            self.application.start(0)
            self.next_update = self.application.get_next_change(0)
        else:
            self.next_update = (self.Events.NONE, None)
            self.off_start_time = 0
        
        self.log_processed = False
        self.log = [{'time' : 0, 
                     'event' : self.Events.NONE.name, 
                     'i_out' : self.get_current(initial_voltage), 
                     'state' : self.state.name,
                     'v_out' : initial_voltage,
                     'v_cap' : initial_cap_voltage}]
        
        self.stats = {'time_ON' : 0,
                      'time_OFF' : 0,
                      'time_SAVE' : 0,
                      'time_RESTORE' : 0,
                      'energy_ON' : 0,
                      'energy_OFF' : 0,
                      'energy_SAVE' : 0,
                      'energy_RESTORE' : 0,
                      'max_off_time' : 0}
        for event in self.Events:
            self.stats[event.name] = 0
                
    def get_state(self):
        return self.state
    
    def set_state(self, state):
        self.state = state
        
    def get_current(self, voltage): #no voltage dependency so far
   
        assert ((self.state != self.States.OFF) and (voltage >= self.v_min)) or \
                (self.state == self.States.OFF), \
            "Error: Load in wrong state, cannot be turned on with this voltage level"
            
        if self.state == self.States.ON:  # if we are on, the appl. gives the current consumption
            return self.application.get_current()
        else:
            return self.currents[self.state]

    def get_next_change(self, time): #
        if self.state == self.States.ON:  # if we are on, the appl. gives the next update event
            next_update = self.application.get_next_change(time)[1]
        else:
            next_update = self.next_update[1]
        return None if next_update == None else next_update - time
                
    def update_state(self, time, dt, input_voltage, cap_voltage):
        
        assert (self.next_update[1] == None) or (time <= self.next_update[1]), "Error: Missed a load update."
        
        if input_voltage > self.v_min:
            cap_voltage_event = self.voltage_monitor.get_event(self.old_cap_voltage, cap_voltage)
            self.old_cap_voltage = cap_voltage
        else:
            cap_voltage_event = None
            self.old_cap_voltage = 0
            
        board_voltage_events = self.voltage_monitor.get_events(self.old_board_voltage, input_voltage)
        board_voltage_event = board_voltage_events[-1] if len(board_voltage_events) > 0 else None
        self.old_board_voltage = input_voltage
        
        load_event = self.next_update[0] if self.next_update[1] != None and time >= self.next_update[1] else None
                
        if cap_voltage_event == None and load_event == None and board_voltage_event == None:
            self.stats[f'time_{self.state.name}'] += dt * self.time_base
            self.stats[f'energy_{self.state.name}'] += input_voltage * self.get_current(input_voltage) * dt * self.time_base
            #We don't log if nothing changes
            # self.log.append({'time' : time, 
            #                   'event' : self.Events.NONE.name, 
            #                   'i_out' : self.get_current(input_voltage), 
            #                   'state' : self.state.name, 
            #                   'v_out' : input_voltage,
            #                   'v_cap' : cap_voltage})
            return #nothing to do
                    
        #Update load's state machine
        if self.state == self.States.ON:
            load_event = self.handle_on_state(time, load_event, cap_voltage_event, board_voltage_event)
        
        elif self.state == self.States.OFF:
            load_event =  self.handle_off_state(time, load_event, cap_voltage_event, board_voltage_event)
              
        elif self.state == self.States.RESTORE: #we did the restoring, so now we are active
            load_event =  self.handle_restore_state(time, load_event, cap_voltage_event, board_voltage_event)
                
        elif self.state == self.States.SAVE: #we saved a checkpoint, so we will sleep now
            load_event = self.handle_save_state(time, load_event, cap_voltage_event, board_voltage_event)
            
                    
        #if load_event != self.Events.NONE:
        if self.log_full:
            self.log.append({'time' : time * self.time_base, 
                             'event' : load_event.name, 
                             'i_out' : self.get_current(input_voltage), 
                             'state' : self.state.name, 
                             'v_out' : input_voltage,
                             'v_cap' : cap_voltage})
            
        self.stats[load_event.name] += 1
        self.stats[f'time_{self.state.name}'] += dt * self.time_base
        self.stats[f'energy_{self.state.name}'] += input_voltage * self.get_current(input_voltage) * dt * self.time_base
        
 
    def handle_restore_state(self, time, load_event, voltage_event, board_voltage_event): 
        assert voltage_event == None or voltage_event == self.voltage_monitor.Events.SAVE, "Error in state machine."
        
        if board_voltage_event == self.voltage_monitor.Events.OFF:
            self.state = self.States.OFF
            self.next_update = (self.Events.NONE, None)
            self.off_start_time = time 
            return self.Events.RESTORE_FAIL
                    
        if voltage_event == self.voltage_monitor.Events.SAVE:
            self.state = self.States.SAVE
            self.next_update = (self.Events.SAVE_SUCCESS, time + self.t_save_s)
        else:
            assert load_event == self.Events.RESTORE_SUCCESS, "Error in state machine."
            self.state = self.States.ON
            self.application.start(time)
            self.next_update = self.application.get_next_change(time)
            if (time - self.off_start_time)*self.time_base > self.stats['max_off_time']:
                self.stats['max_off_time'] = (time - self.off_start_time) * self.time_base
                 
        return load_event if load_event == self.Events.RESTORE_SUCCESS else self.Events.RESTORE_FAIL
    
    def handle_save_state(self, time, load_event, voltage_event, board_voltage_event): #from save we move to off 
        if load_event == self.voltage_monitor.Events.RESTORE:
            self.state = self.States.RESTORE
            self.next_update = (self.Events.RESTORE_SUCCESS, time + self.t_restore_s)
            print("Moved from save directly to restoring!")
        else:
            assert (load_event == self.Events.SAVE_SUCCESS) or (board_voltage_event == self.voltage_monitor.Events.OFF), "Error in state machine."
            self.state = self.States.OFF
            self.next_update = (self.Events.NONE, None)

        return load_event if load_event == self.Events.SAVE_SUCCESS else self.Events.SAVE_FAIL
        
        
    def handle_off_state(self, time, load_event, voltage_event, board_voltage_event): #from off we can only move to restore states  
    
        if board_voltage_event == self.voltage_monitor.Events.OFF or voltage_event == self.voltage_monitor.Events.SAVE: #ignore off and save threshold since we are anyway off
            return self.Events.NONE

        assert voltage_event == self.voltage_monitor.Events.RESTORE, "Error in state machine: expected restore trigger."
    
        self.state = self.States.RESTORE
        self.next_update = (self.Events.RESTORE_SUCCESS, time + self.t_restore_s)
        return self.Events.RESTORE_START
    
    def handle_on_state(self,  time, load_event, voltage_event, board_voltage_event):
        assert voltage_event != self.voltage_monitor.Events.OFF, "Error in state machine: missed voltage update."
        
        #handle application first
        if load_event == self.Events.APPLICATION_EVENT:
            self.application.proceed(time)
            self.next_update = self.application.get_next_change(time)
            
        if board_voltage_event == self.voltage_monitor.Events.OFF:
            self.application.stop(time)
            self.state = self.States.OFF
            self.next_update = (self.Events.NONE, None)
            self.off_start_time = time
            return self.Events.FORCED_OFF
        
        assert self.old_board_voltage > self.v_min, "Error in state machine: missed board voltage update."
        
        if voltage_event == self.voltage_monitor.Events.RESTORE:
            return load_event #ignore restoring treshold as there's nothing to restore
                
        if voltage_event == self.voltage_monitor.Events.SAVE:
            self.state = self.States.SAVE
            self.next_update = (self.Events.SAVE_SUCCESS, time + self.t_save_s) #overwrite update from scheduler because we need to save
            self.application.stop(time)
            self.off_start_time = time
            return self.Events.SAVE_START
        
        assert (load_event == self.Events.APPLICATION_EVENT) or (load_event == self.Events.NONE), "Error in state machine."
        return load_event
    
    def process_log(self, time_max):
        if self.log_full:
            self.log = pd.DataFrame(self.log)
            self.log.loc[:, 'dt'] = abs(self.log.time.diff(-1))
            self.log.loc[self.log.index[-1], 'dt'] = time_max*self.time_base - self.log.time.iloc[-1]
            self.log.loc[:,'p_out'] = self.log.i_out * (self.log.v_out.shift(-1) + self.log.v_out)/2 #interpolate/estimate power consumption between two different voltage points
        self.log_processed = True
        self.application.process_log(time_max)
        
    def get_log(self):      
        return self.log
    
    def get_log_stats(self):    
                
        return self.stats
        #TODO! Additional stats are not properly implemented/tested yet
        #normalize for fair comparison forward progress/reactivity comparison
        # self.log = self.log[self.log.index <= self.log[self.log.state == 'RESTORE'].index.max()].copy() #copy to avoid python warnings
        
        # if 'ON' in self.log.state.unique():
        #     #Extract stats
        #     reactivity = self.log[self.log.event == 'RESTORE_SUCCESS'].time.diff().max()
        #     grouped_sum = self.log.groupby('state').dt.sum()
        #     grouped_count = self.log.groupby('state').dt.count()
            
        #     total_energy = (self.log['p_out'] * self.log['dt']).sum()
        #     total_useful_energy = (self.log[self.log.state=='ON']['p_out'] * self.log[self.log.state=='ON']['dt']).sum()
        #     if self.Events.SAVE_FAIL in self.log.event.unique() or self.Events.RESTORE_FAIL in self.log.event.unique():
        #         forward_progress = 0
        #         total_useful_energy = 0 #not useful if we redo the same computation all the time
        #     else:
        #         forward_progress = grouped_sum.ON / grouped_sum.sum()
                
        #     return {
        #         'time_total' : grouped_sum.sum(),
        #         'time_on' : grouped_sum.ON,
        #         'time_off' : grouped_sum.OFF,
        #         'num_saves' : grouped_count.SAVE,
        #         'num_restores' : grouped_count.RESTORE,
        #         'forward_progress': forward_progress,
        #         'reactivity' : reactivity,
        #         'total_energy' : total_energy,
        #         'total_useful_energy' : total_useful_energy}
        
        # else:
        #     return {
        #         'time_total' : self.log.dt.sum(),
        #         'time_on' : 0,
        #         'time_off' : 0,
        #         'num_saves' : 0,
        #         'num_restores' : 0,
        #         'forward_progress': 0,
        #         'reactivity' : 0,
        #         'total_energy' : (self.log['p_out'] * self.log['dt']).sum(),
        #         'total_useful_energy' : 0}
      
    
    #classes for different applications
    
    class Computation:
        
        def __init__(self, config, verbose, time_base):
            if verbose:
                print("Create Computation application.")
                
            self.i_active = config['i_active']
            self.reset()
        
        def get_current(self):
            return self.i_active 
        
        def start(self, time):
            pass
        
        def stop(self, time):
            pass

        def get_next_change(self, time): 
            return (AdvancedJITLoad.Events.NONE, None)
        
        def proceed(self, time):
            pass
        
        def reset(self):
            self.log = [] #TODO: convert to numpy tuple (faster)
        
        def get_log(self):
            return pd.DataFrame(self.log) #todo: check and remove, as data also accesible from Load log (total_time = time in state Active)
        
        def process_log(self, time_max):
            pass
        
    class Atomic:
        def __init__(self, config, verbose, time_base):
            if verbose:
                print("Create Atomic application.")
            self.time_base = time_base   
            self.log_full = config['log'] if 'log' in config else True
                
            self.i_active = config['i_active']
            self.t_active = int(config['t_task'] / self.time_base)
            self.reset()
            
            
        def reset(self):
            self.next_update = None
            self.log = [] #TODO: convert to numpy tuple (faster)
            self.log_processed = False
            self.stats = {'num_tasks_successful' : 0,
                          'num_tasks_failed' : 0}
      
        def get_current(self):
            return self.i_active #if we are active, we try to compute
        
        def start(self, time): 
            assert self.next_update == None, "Error in load state machine. Application was not stopped."
            self.next_update = time + self.t_active #we restart at power-up
            if self.log_full:
                self.log.append({'start' : time * self.time_base, 'end' : time* self.time_base, 'success' : False, 'active' : True, 'restart' : True}) 
                        
        def stop(self, time):
            if self.log_full:
                self.log[-1]['end'] = time * self.time_base
                self.log[-1]['success'] = (time == self.next_update) 
            if time >= self.next_update: 
                self.stats['num_tasks_successful'] += 1
            else:
                self.stats['num_tasks_failed'] += 1

            self.next_update = None
            
        def proceed(self, time):
            if time > self.next_update: #store success of running task and start new one 
                if self.log_full:
                    self.log[-1]['end'] = time * self.time_base
                    self.log[-1]['success'] = True
                    self.log.append({'start' : time * self.time_base, 'end' : 0, 'success' : False, 'active' : True}) #start next task
                self.next_update = time + self.t_active
                self.stats['num_tasks_successful'] += 1
                
        def get_next_change(self, time): 
            return (AdvancedJITLoad.Events.APPLICATION_EVENT, self.next_update)
        
        def process_log(self, time_max):
            if self.log_full:
                self.log = pd.DataFrame(self.log)
                self.log.loc[self.log.index[-1], "end"] = time_max * self.time_base
                self.log['dt'] = self.log.end - self.log.start
            else:
                self.log = pd.DataFrame()
              
        def get_log(self):
            return self.log
        
        def get_stats(self):
            return self.stats
        
#TODO!     
    # class Periodic:
    #     def __init__(self, config, verbose):
    #         if verbose:
    #             print("Create Periodic application.")
    #         self.i_active = config['i_active']
    #         self.t_active = config['t_task']
    #         self.p_active = config['p_task']
    #         self.p_margin = config['p_margin'] if 'p_margin' in config else 0
    #         self.i_sleep  = config['i_sleep']
    #         self.reset()
            
    #     def reset(self):
    #         self.next_update = None
    #         self.active = False
    #         self.log = [] #TODO: convert to numpy tuple (faster)
        
    #     def get_current(self):
    #         return self.i_active if self.active else self.i_sleep
        
    #     def start(self, time): 
    #         assert self.next_update == None, "Error in load state machine. Application was not stopped."
    #         # TODO: add margin for start of task!
    #         if time % self.p_active == 0:
    #             self.active = True
    #             self.next_update = time + self.t_active
    #         else:
    #             self.active = False
    #             self.next_update = time + self.p_active - time % self.p_active
                
    #         self.log.append({'start' : time, 'end' : 0, 'success' : False, 'active' : self.active})
                        
    #     def stop(self, time):
    #         self.log[-1]['success'] = not self.active or (time == self.next_update) #if app is inactive, it cannot fail
    #         self.log[-1]['end'] = time
    #         self.active = False
    #         self.next_update = None
            
    #     def proceed(self, time):
    #         if time >= self.next_update: #application state changes
    #             #store success of running tas/sleeping   
    #             self.log[-1]['end'] = time
    #             self.log[-1]['success'] = True
    #             if self.active and self.t_active != self.p_active: #old task succeded, go to sleep and wait for next one
    #                 self.active = False
    #                 self.next_update = time + self.p_active - time % self.p_active
    #             else: # we were inactive (or cannot go to sleep) and need to start next task.                  
    #                 self.active = True
    #                 self.next_update = time + self.t_active
                    
    #             self.log.append({'start' : time, 'end' : time, 'success' : False, 'active' : self.active})
                
    #     def get_next_change(self, time): 
    #         return (JITLoad.Events.APPLICATION_EVENT, self.next_update)
        
        
    #     def process_log(self, time_max):
    #         self.log = pd.DataFrame(self.log)
    #         self.log.loc[self.log.index[-1], "end"] = time_max
    #         self.log['dt'] = self.log.end - self.log.start
        
    #     def get_log(self):
    #         return self.log
        
    #     def get_stats(self):
    #         log = self.get_log() 
    #         stats = {'tasks_success' : len(log[log.active & log.success]),
    #                  'tasks_failed' : len(log[log.active & ~log.success]),
    #                  'time_active_sucess' : log[log.active & log.success].dt.sum(),
    #                  'time_active_failed' : log[log.active & ~log.success].dt.sum(),
    #                  'time_sleeping' : log[~log.active].dt.sum()                         #todo: #missed tasks in a row?
    #             }
    #         return stats