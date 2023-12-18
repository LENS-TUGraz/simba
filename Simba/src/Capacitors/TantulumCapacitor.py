# -*- coding: utf-8 -*-
"""
Capacitor module implementation:

Tantulum capacitor

The `TantulumCapacitor` module describes a capacitor 
of the AVX TAJ series with a certain capacitance and voltage ratings. 
In contrast to an ideal capacitor, tantulum capacitors exhibit leakage currents 
that depend on (i) the capacitance, (ii) the rated voltage, 
and (iii) the applied voltage. This behavior is modelled according 
to the AVX technical notes and accounted for in the charge/discharge behavior of the capacitor.

For more details on the leakage modeling, see: 

- *Low Leakage Current Aspect of Designing with  Tantalum and Niobium Oxide Capacitors*: https://www.avx.com/docs/techinfo/Low_Leakage_Current_Aspect_Designing_Tantalum_Niobium_Oxide_Capacitors.pdf).
- Jie Zhan et al. *Exploring the Effect of Energy Storage Sizing on Intermittent
Computing System Performance*. IEEE Trans. on Computer-Aided Design of
Integrated Circuits and Systems (2022).

"""

from IdealCapacitor import IdealCapacitor

class TantalumCapacitor(IdealCapacitor):
   
    def __init__(self, config, verbose, time_base):
        self.verbose = verbose
        if verbose:
            print("Create Tantulum Capacitor.")
        
        self.log_full = config['log'] if 'log' in config else True
        self.capacitance = config['capacitance']
        self.voltage_rated = config['v_rated']
        self.voltage_initial = config['v_initial'] if 'v_initial' in config else 0
        self.time_base = time_base
                
    def get_leakage(self, i = 0):
        #leakage only depending on current operating voltage, rest is fixed (so far)
        leakage_ratio_tantal = 0.05 * 20 ** (2.25 / self.voltage_rated) #see 'Exploring the Effect of Energy Storage Sizing on Intermittent Computing System Performance'
        i_leakage = self.capacitance * 0.01 * self.voltage_rated * leakage_ratio_tantal
        return i_leakage * self.voltage
    
