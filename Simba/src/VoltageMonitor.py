# -*- coding: utf-8 -*-
"""
Helper class: Voltage monitor 

Trigger events if (registered) voltage thresholds are crossed.
"""

	
from sortedcontainers import SortedDict
from multipledispatch import dispatch
from aenum import Enum, extend_enum

class VoltageMonitor:
    
    def __init__(self, default_thresholds = []):
        self.default_thresholds = default_thresholds
        self.reset()
    
    def reset(self):
        self.thresholds_rising = SortedDict()
        self.thresholds_falling = SortedDict()
        self.Events = Enum("Events", [])
        self.register_events(self.default_thresholds)
        
    def register_event(self, name, v_threshold, edge):
        
        try:
            extend_enum(self.Events, name)
        except:
            pass
        
        if edge in ['rising', 'both']:
            self.thresholds_rising[v_threshold] = self.Events[name]
            
        if edge in ['falling', 'both']:
            self.thresholds_falling[v_threshold] = self.Events[name]
        
    def register_events(self, evt_list):
        for evt in evt_list:
            self.register_event(evt[0], evt[1], evt[2]) #0...name, 1...threshold, 2...edge
    
    @dispatch(str)
    def unregister_event(self, name):
        if self.Events[name] in self.thresholds_falling.values():
            del self.thresholds_falling[self.thresholds_falling.keys()[self.thresholds_falling.values().index(self.Events[name])]]

        if self.Events[name] in self.thresholds_rising.values():
            del self.thresholds_rising[self.thresholds_rising.keys()[self.thresholds_rising.values().index(self.Events[name])]]
            
    @dispatch(float)       
    def unregister_event(self, voltage):
        if voltage in self.thresholds_falling:
            del self.thresholds_falling[voltage]
        if voltage in self.thresholds_rising:
            del self.thresholds_rising[voltage]
    
    #return voltage value of next threshold that we reach from the current voltage when charging/discharging
    def get_next_threshold(self, voltage, i):
        if i < 0 and len(self.thresholds_falling.keys()) > 0 and voltage > self.thresholds_falling.keys()[0]:
            # get elements that are > old_voltage 
            # check if new_voltage is larger, if yes return the corresponding name
            return self.thresholds_falling.peekitem(self.thresholds_falling.bisect_left(voltage) - 1)[0]
            
        elif i > 0 and len(self.thresholds_rising.keys()) > 0 and voltage < self.thresholds_rising.keys()[-1]:
            # get elements that are < old_voltage 
            # check if new_voltage is smaller, if yes return the corresponding name
            return self.thresholds_rising.peekitem(self.thresholds_rising.bisect_right(voltage))[0]

        return None
    
    #return the name of the threshold that has been crossed in the last period --> should only be one, since only one can be handled at the time anyway!
    def get_event(self, old_voltage, new_voltage):
        if old_voltage < new_voltage:
            nt = self.get_next_threshold(old_voltage, 1)    #next threshold for charging
            if nt != None and new_voltage >= nt:            #return name if we crossed the threshold 
                return self.thresholds_rising[nt]
            
        elif old_voltage > new_voltage:
            nt = self.get_next_threshold(old_voltage, -1)    #next threshold for discharging
            if nt != None and new_voltage <= nt:            #return name if we crossed the threshold 
                return self.thresholds_falling[nt]
        return None
    
    def get_events(self, old_voltage, new_voltage):
        events = []
        if old_voltage < new_voltage:
            nt = self.get_next_threshold(old_voltage, 1)    #next threshold for charging
            while nt != None and new_voltage >= nt:
                events.append(self.thresholds_rising[nt])   #store if we crossed the threshold
                nt = self.get_next_threshold(nt, 1)
            
        elif old_voltage > new_voltage:
            nt = self.get_next_threshold(old_voltage, -1)    #next threshold for discharging
            while nt != None and new_voltage <= nt:
                events.append(self.thresholds_falling[nt])   #store if we crossed the threshold
                nt = self.get_next_threshold(nt, -1)
        
        return events

    
