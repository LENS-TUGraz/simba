# -*- coding: utf-8 -*-
"""
Load module implementation:

JITLoad

TODO: description
"""

from aenum import Enum
import pandas as pd
from VoltageMonitor import VoltageMonitor
                   
class JITLoad:
    
    States = Enum("State", ['OFF', 'RESTORE', 'COMPUTE', 'CHECKPOINT'])
    Events = Enum("Events", ['NONE', 'RESTORE_START', 'RESTORE_SUCCESS', 'RESTORE_FAIL', 'CHECKPOINT_START', 'CHECKPOINT_FAIL', 'CHECKPOINT_SUCCESS', 'COMPUTE_START', 'TURN_OFF'])
     
    def __init__(self, config, verbose, time_base):
        
        self.verbose = verbose
        if verbose:
            print("Create Engage load.")
            
        self.time_base = time_base
            
        self.log_full = config['log'] if 'log' in config else True
        self.verbose_log = config['verbose_log'] if 'verbose_log' in config else False
            
        self.v_off = config['v_off']
        self.v_on = config['v_on']
        self.v_checkpoint = config['v_checkpoint']
    
        self.currents = dict()
        for state in self.States:
              self.currents[state] = config['currents'][state.name] if state.name in config['currents'] else 0
        
        self.t_checkpoint = config['t_checkpoint']
        self.t_checkpoint_period = config['t_checkpoint_period']
        self.t_restore = config['t_restore']
        self.t_restore_startup = config['t_restore_startup']


                          
    def reset(self, initial_voltage, initial_cap_voltage):
        self.old_voltage = initial_voltage
        
        self.voltage_monitor = VoltageMonitor(self.create_thresholds())
        self.voltage_monitor.reset()
        
        self.t_checkpoint_s = int(self.t_checkpoint / self.time_base)
        self.t_checkpoint_period_s = int(self.t_checkpoint_period / self.time_base)
        self.t_restore_s = int(self.t_restore / self.time_base)
        self.t_restore_startup_s = int(self.t_restore_startup / self.time_base)
        
        self.initial_checkpoint_done = False #to account for long startup time at first boot
        
        if initial_voltage > self.v_off:
            self.state = self.States.RESTORE
            self.voltage_monitor.unregister_event('ON')
            self.next_update = (self.Events.RESTORE_SUCCESS, self.t_restore_s) #after restore, move to compute
        else:
            self.state = self.States.OFF
            self.next_update = (self.Events.NONE, None)
            self.voltage_monitor.unregister_event('OFF')
            self.voltage_monitor.unregister_event('CHECKPOINTS_START')
                                
        self.log_processed = False
        self.log = [{'time' : 0, 
                     'event' : self.Events.NONE.name, 
                     'i_out' : self.get_current(initial_voltage), 
                     'state' : self.state.name,
                     'v_out' : initial_voltage,
                     'v_cap' : initial_cap_voltage,
                     'valid_checkpoint' : False}]
        
        self.stats = {'time_OFF' : 0,
                      'time_RESTORE' : 0,
                      'time_COMPUTE' : 0,
                      'time_CHECKPOINT' : 0,
                      'energy_RESTORE' : 0,
                      'energy_OFF' : 0,
                      'energy_COMPUTE' : 0,
                      'energy_CHECKPOINT' : 0,
                      'num_CHECKPOINT_successful' : 0,
                      'num_CHECKPOINT_failed' : 0,
                      'num_RESTORE_successful' : 0,
                      'num_RESTORE_failed' : 0}
        
    def create_thresholds(self):
        thresholds = [("OFF", self.v_off, "falling"),
                      ("CHECKPOINTS_START", self.v_checkpoint, "falling"),
                      ("ON", self.v_on, "rising")] #todo: make it work that both rising and falling edge of this voltage trigger a simulation round
        return thresholds
                
    def get_state(self):
        return self.state
    
    def set_state(self, state):
        self.state = state
        
    def get_current(self, voltage): #no voltage dependency so far
   
        assert ((self.state != self.States.OFF) and (voltage >= self.v_off)) or \
                (self.state == self.States.OFF), \
            f"Error: Load in wrong state, cannot be turned on with this voltage level ({voltage} in state {self.state})"

        return self.currents[self.state]

    def get_next_change(self, time): #
        next_update = self.next_update[1]
        return None if next_update == None else next_update - time
                
    def update_state(self, time, dt, input_voltage, cap_voltage):
        
        assert (self.next_update[1] == None) or (time <= self.next_update[1]), "Error: Missed a load update."
        
        self.stats[f'time_{self.state.name}'] += dt * self.time_base
        self.stats[f'energy_{self.state.name}'] += (self.old_voltage + input_voltage) / 2 * self.get_current(self.old_voltage) * dt * self.time_base
        
        load_event = self.next_update[0] if self.next_update[1] != None and self.next_update[1] == time else None
        voltage_event = self.voltage_monitor.get_event(self.old_voltage, input_voltage)

        self.old_voltage = input_voltage
   
        if voltage_event == None and load_event == None and (cap_voltage > self.v_checkpoint or input_voltage < self.v_off):
            #We don't log if nothing changes
            if self.verbose_log:
                self.log.append({'time' : time * self.time_base, 
                                  'event' : self.Events.NONE.name, 
                                  'i_out' : self.get_current(input_voltage), 
                                  'state' : self.state.name, 
                                  'v_out' : input_voltage,
                                  'v_cap' : cap_voltage})
            return #nothing to do
        
        if voltage_event == self.voltage_monitor.Events.OFF: #todo: account for hysteresis in voltage manager
            load_event = self.turn_off(time, load_event)
            
        elif voltage_event == self.voltage_monitor.Events.ON:
            load_event = self.turn_on(time, load_event, cap_voltage)
            
        else:
            load_event = self.continue_application(time, load_event, cap_voltage)
                
            
        if load_event != self.Events.NONE:
            if self.log_full:
                self.log.append({'time' : time * self.time_base, 
                                 'event' : load_event.name, 
                                 'i_out' : self.get_current(input_voltage), 
                                 'state' : self.state.name, 
                                 'v_out' : input_voltage,
                                 'v_cap' : cap_voltage,
                                 'valid_checkpoint' : False})
            
 
    def turn_off(self, time, load_event):
        
        if load_event == None: #we didn't finish the previous task; just log the fail
            if self.state == self.States.CHECKPOINT:
                self.stats['num_CHECKPOINT_failed'] += 1
                event = self.Events.CHECKPOINT_FAIL
            elif self.state == self.States.RESTORE:
                self.stats['num_RESTORE_failed'] += 1
                event = self.Events.RESTORE_FAIL
            else:
                event = self.Events.TURN_OFF
        else:
            if self.state == self.States.CHECKPOINT:
                self.stats['num_CHECKPOINT_successful'] += 1
                self.checkpoint_done = True
                assert self.log[-2]['state'] == "COMPUTE", "Error in state machine."
                self.log[-2]['valid_checkpoint'] = True
            event = self.Events.TURN_OFF
            
        self.state = self.States.OFF    
        self.next_update = (self.Events.NONE, None)
        self.voltage_monitor.unregister_event('OFF')
        self.voltage_monitor.unregister_event('CHECKPOINTS_START')
        self.voltage_monitor.register_event('ON', self.v_on, 'rising') 
            
        return event
    
    def turn_on(self, time, load_event, cap_voltage):
        
        assert load_event == None, "Error in state machine. In OFF mode the load is not expecting an event."
        
        self.voltage_monitor.unregister_event('ON')
        self.voltage_monitor.register_event('OFF', self.v_off, 'falling')  
        
        #after turning on, we restore and then move to compute; at first boot, the restore time is longer then after checkpointing
        self.state = self.States.RESTORE
        self.next_update = (self.Events.RESTORE_SUCCESS, time + self.t_restore_s if self.initial_checkpoint_done else time + self.t_restore_startup_s)
        
                
        return self.Events.RESTORE_START
                
    def continue_application(self, time, load_event, cap_voltage):
        
        assert load_event != self.Events.NONE or cap_voltage <= self.v_checkpoint, "Something went wrong."
        
        if cap_voltage <= self.v_checkpoint and self.next_update[1] == None: #we hit the checkpoint threshold for the first time, let's make a checkpoint
            assert self.state == self.States.COMPUTE, "Error."
            load_event = self.Events.CHECKPOINT_START
        
        if load_event == self.Events.CHECKPOINT_START:
            assert self.state == self.States.COMPUTE or self.state == self.States.RESTORE, "Error: Load can start checkpointing only after computing or restoring."
            self.state = self.States.CHECKPOINT
            self.next_update = (self.Events.CHECKPOINT_SUCCESS, time + self.t_checkpoint_s)
            
        elif load_event == self.Events.CHECKPOINT_SUCCESS:
            assert self.state == self.States.CHECKPOINT, "Error: Load has to be in Checkpoint state."
            self.initial_checkpoint_done = True
            self.stats['num_CHECKPOINT_successful'] += 1
            self.state = self.States.COMPUTE
            assert self.log[-2]['state'] == "COMPUTE", "Error in state machine/logging."
            self.log[-2]['valid_checkpoint'] = True
            #From now on, we perform checkpoints periodically until we restart (disable voltage interrupt to avoid oscillation)
            self.next_update = (self.Events.CHECKPOINT_START, time + self.t_checkpoint_period_s)
            self.voltage_monitor.unregister_event("CHECKPOINTS_START")
                
        elif load_event == self.Events.RESTORE_SUCCESS:
            assert self.state == self.States.RESTORE, "Error: Load must be in Restore state"
            self.stats['num_RESTORE_successful'] += 1
            self.state = self.States.COMPUTE #after restoring, we can move to compute state
            
            self.voltage_monitor.register_event('CHECKPOINTS_START', self.v_checkpoint, 'falling')
            if cap_voltage <= self.v_checkpoint:
                self.next_update = (self.Events.CHECKPOINT_START, time + 1) #move to checkpointing fast!
            else:
                self.next_update = (self.Events.NONE, None) #let's stay in compute state
                                
        return load_event if load_event != None else self.Events.NONE
    
    def process_log(self, time_max):
        if self.log_full:
            self.log = pd.DataFrame(self.log)
            self.log.loc[:, 'dt'] = abs(self.log.time.diff(-1))
            self.log.loc[self.log.index[-1], 'dt'] = time_max * self.time_base - self.log.time.iloc[-1]
            self.log.loc[:,'p_out'] = self.log.i_out * (self.log.v_out.shift(-1) + self.log.v_out)/2 #interpolate/estimate power consumption between two different voltage points
        else:
            self.log = pd.DataFrame()
        self.log_processed = True
        
    def get_log(self):      
        return self.log
    
    def get_log_stats(self, normalize = True):      
    
        load_log = self.log[(self.log.event != 'NONE') | (self.log.time == 0)].reset_index(drop=True).copy()
        #Filter to make statistics comparable
        if normalize:
            
            try:
                start_idx = load_log[load_log.state == 'RESTORE'].index[0]
                end_idx = load_log[load_log.state == 'RESTORE'].index[-1]
                load_log = load_log.iloc[start_idx : end_idx].copy()
                load_log = load_log.reset_index(drop=True)
                                
            except:
                pass
        
        if not load_log.empty:      
            #update dt and p_out accordingly (if we have removed 'NONE' events)
            #last_time = load_log.iloc[-1]['time'] #we need to store the last dt
            load_log.loc[:,'dt'] = abs(load_log.time.diff(-1))   
            #load_log.loc[load_log.index[-1], 'dt'] = last_time - load_log.iloc[-1].time
            load_log.loc[:,'p_out'] = load_log.i_out * (load_log.v_out.shift(-1) + load_log.v_out)/2 #interpolate/estimate power consumption between two different voltage points
            load_log.loc[load_log.index[-1],'p_out'] = load_log.iloc[-1].i_out * load_log.iloc[-1].v_out
            
            #If we filter/crop, we also need to update the accumulative values:
            if normalize:
                for state in ['OFF', 'RESTORE', 'COMPUTE', 'CHECKPOINT']:
                    self.stats[f'time_{state}'] = load_log[load_log.state == state].dt.sum()
                    self.stats[f'energy_{state}'] = (load_log[load_log.state == state].p_out * load_log[load_log.state == state].dt).sum()
                    
                self.stats['num_CHECKPOINT_successful_norm'] = len(load_log[load_log.event == 'CHECKPOINT_SUCCESS'])
                self.stats['num_CHECKPOINT_failed_norm'] = len(load_log[load_log.event == 'CHECKPOINT_FAIL'])
                self.stats['num_RESTORE_successful'] = len(load_log[load_log.event == 'RESTORE_SUCCESS'])
                self.stats['num_RESTORE_failed'] = len(load_log[load_log.event == 'RESTORE_FAIL'])
            
            states_compute_useful = load_log[((load_log.state == 'COMPUTE') & load_log.valid_checkpoint) | ((load_log.state == 'COMPUTE') & (load_log.index >= load_log.index.max() -1))]
            
            self.stats['num_COMPUTE_useful'] = len(states_compute_useful)
            
            self.stats['time_COMPUTE_useful'] = states_compute_useful.dt.sum()
            self.stats['energy_COMPUTE_useful'] = (states_compute_useful.p_out * states_compute_useful.dt).sum()
            self.stats['forward_progress'] = self.stats['time_COMPUTE_useful'] / (self.stats['time_COMPUTE'] + self.stats['time_CHECKPOINT'] + self.stats['time_RESTORE'] + self.stats['time_OFF'])
                
            self.stats['time_off_mean'] = load_log[load_log.state == 'OFF'].dt.mean()
            self.stats['time_off_max'] = load_log[load_log.state == 'OFF'].dt.max()
            
            #Get stats from the time between two computing tasks --> time we are unresponsive and user cannot do anything (off + restore)
            #compute_states = load_log[(load_log.state == 'COMPUTE') & load_log.valid_checkpoint]
            
            self.stats['time_unavailable_95'] = (load_log[load_log.state == 'OFF'].dt.reset_index() + load_log[load_log.state == 'RESTORE'].dt.reset_index()).dt.quantile(0.95)
            self.stats['time_unavailable_mean'] = (load_log[load_log.state == 'OFF'].dt.reset_index() + load_log[load_log.state == 'RESTORE'].dt.reset_index()).dt.mean()
            self.stats['time_unavailable_max'] =  (load_log[load_log.state == 'OFF'].dt.reset_index() + load_log[load_log.state == 'RESTORE'].dt.reset_index()).dt.max()
                 

            if len(load_log[load_log.state == 'RESTORE']) > 1:
                # Get stats from time where user can play (including checkpoints, since they are so short)
                self.stats['time_available_95'] = (load_log[load_log.state == 'RESTORE'].time.diff().reset_index().time - load_log[load_log.state == 'RESTORE'].reset_index().dt - load_log[load_log.state == 'OFF'].reset_index().dt).quantile(0.95)
                self.stats['time_available_mean'] = (load_log[load_log.state == 'RESTORE'].time.diff().reset_index().time - load_log[load_log.state == 'RESTORE'].reset_index().dt - load_log[load_log.state == 'OFF'].reset_index().dt).mean()
                self.stats['time_available_max'] =  (load_log[load_log.state == 'RESTORE'].time.diff().reset_index().time - load_log[load_log.state == 'RESTORE'].reset_index().dt - load_log[load_log.state == 'OFF'].reset_index().dt).max()
                self.stats['time_available_min'] =  (load_log[load_log.state == 'RESTORE'].time.diff().reset_index().time - load_log[load_log.state == 'RESTORE'].reset_index().dt - load_log[load_log.state == 'OFF'].reset_index().dt).min()
                
                self.stats['time_on_mean'] = (load_log[load_log.state == 'RESTORE'].time.diff().reset_index().time - load_log[load_log.state == 'OFF'].reset_index().dt).mean()
                self.stats['time_on_max'] =  (load_log[load_log.state == 'RESTORE'].time.diff().reset_index().time - load_log[load_log.state == 'OFF'].reset_index().dt).max()
            else:
                #only one active phase
                self.stats['time_available_95'] = load_log[load_log.state == 'COMPUTE'].dt.sum() + load_log[load_log.state == 'CHECKPOINT'].dt.sum()
                self.stats['time_available_mean'] = load_log[load_log.state == 'COMPUTE'].dt.sum() + load_log[load_log.state == 'CHECKPOINT'].dt.sum()
                self.stats['time_available_max'] =  load_log[load_log.state == 'COMPUTE'].dt.sum() + load_log[load_log.state == 'CHECKPOINT'].dt.sum()
                self.stats['time_available_min'] =  load_log[load_log.state == 'COMPUTE'].dt.sum() + load_log[load_log.state == 'CHECKPOINT'].dt.sum()
                
                self.stats['time_on_mean'] = load_log[load_log.state == 'COMPUTE'].dt.sum() + load_log[load_log.state == 'CHECKPOINT'].dt.sum() + load_log[load_log.state == 'RESTORE'].dt.sum()
                self.stats['time_on_max'] =  load_log[load_log.state == 'COMPUTE'].dt.sum() + load_log[load_log.state == 'CHECKPOINT'].dt.sum() + load_log[load_log.state == 'RESTORE'].dt.sum()

            try:
                self.stats['time_compute_mean'] = states_compute_useful.dt.mean()
            except:
                self.stats['time_compute_mean'] = 0
                
        else: #No logging data, we cannot compute additional statistics
            self.stats['time_compute_mean'] = None
            self.stats['time_off_mean'] = None
            self.stats['time_off_max'] = None
            self.stats['forward_progress'] = None
            self.stats['time_COMPUTE_useful'] = None
            
        self.stats['energy_total'] =  self.stats['energy_OFF'] + self.stats['energy_COMPUTE'] + self.stats['energy_RESTORE'] + self.stats['energy_CHECKPOINT']
        self.stats['time_total'] =  self.stats['time_OFF'] + self.stats['time_COMPUTE'] + self.stats['time_RESTORE'] + self.stats['time_CHECKPOINT']
        return self.stats