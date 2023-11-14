# Configuration(s) for simulation
LOG = True

# Color map to plot the load's states accordingly
color_map = {'INIT': 'yellow',
             'SENSE' : 'blue',
             'SEND' : 'orange',
             'SLEEP' : 'green',
             'BURN' : 'darkgreen',
             'OFF' : 'white'}

# Measured capacitances of used capacitors (nominal (uF) : real (F))
cap_values = {100 : 111e-6,
              47 : 58e-6,
              22 : 23e-6,
              10 : 11e-6}

# Constant current harvesting
harvest_config = {
    'type' :  'Artificial',
    'settings' : {'shape' : 'const',
                  'i_high' : 700e-6}
    }

#Solar harvesting
harvest_config_solar = {'type'       : 'IVCurve',
            'settings'   : {'file'       : 'KXOB25-02-X8F_lux20000.json',
                          'log' : LOG
                          }}

# Default: Application 'burns' energy after sensing (remain in reception mode instead of sleep mode)
load_config_burn = {
    'type' : 'TaskLoad',
    'name' : 'Load_Burn',
    'settings' : { 'tasks' : [{'name': 'INIT',  't' : 2.3e-3,   'i': 600e-6},
                              {'name': 'SENSE', 't' : 0.75e-3,   'i': 700e-6}, 
                              {'name': 'SEND',  't' : 7.25e-3,   'i': 1960e-6},
                              {'name': 'BURN',  't' : 10000000, 'i': 3140e-6}],  #this task (in RX mode) runs basically forever to deplete energy in the capacitor
                    'skip_initial_task' : 1,
                    'v_on' : 1.9,
                    'v_off' : 1.8,
                    'i_off' : 0, #fully turned off anyway
                    'log' : LOG}
    }

# Case 2: Applicaton repeats sensing and sending if there's energy left
load_config_loop = {
    'type' : 'TaskLoad',
    'name' : 'Load_Loop',
    'settings' : { 'tasks' : [{'name': 'INIT',  't' : 2.3e-3,   'i': 600e-6},
                              {'name': 'SENSE', 't' : 0.75e-3,   'i': 700e-6}, 
                              {'name': 'SEND',  't' : 7.25e-3,   'i': 1960e-6}], 
                    'skip_initial_task' : 1,
                    'v_on' : 1.9,
                    'v_off' : 1.8,
                    'i_off' : 0, #fully turned off anyway
                    'log' : True}
    }


# Case 3 (long sensing): Applicaton 'burns' energy after extended sensing (remain in reception mode instead of sleep mode)
load_config_loop_new = {
    'type' : 'TaskLoad',
    'name' : 'Load_Loop',
    'settings' : { 'tasks' : [{'name': 'INIT',  't' : 2.3e-3,   'i': 600e-6},
                              {'name': 'SENSE', 't' : 75e-3,   'i': 700e-6},
                              {'name': 'SEND',  't' : 7.25e-3,   'i': 1960e-6}], 
                    'skip_initial_task' : 1,
                    'v_on' : 1.9,
                    'v_off' : 1.8,
                    'i_off' : 0, #fully turned off anyway
                    'log' : LOG}
    }


# Case 4 (long sensing): Applicaton repeats sensing and sending if there's energy left
load_config_burn_new = {
    'type' : 'TaskLoad',
    'name' : 'Load_Burn',
    'settings' : { 'tasks' : [{'name': 'INIT',  't' : 2.3e-3,   'i': 600e-6},
                              {'name': 'SENSE', 't' : 75e-3,   'i': 700e-6},
                              {'name': 'SEND',  't' : 7.25e-3,   'i': 1960e-6},
                              {'name': 'BURN',  't' : 10000000, 'i': 3140e-6}],  #this task (in RX mode) runs basically forever to deplete energy in the capacitor
                    'skip_initial_task' : 1,
                    'v_on' : 1.9,
                    'v_off' : 1.8,
                    'i_off' : 0, #fully turned off anyway
                    'log' : LOG}
    }

# Case 5 (long sensing): Load turns itself off after one operation cycle
load_config_shutoff = {
    'type' : 'TaskLoad',
    'name' : 'Load_Shut',
    'settings' : { 'tasks' : [{'name': 'INIT',  't' : 2.3e-3,   'i': 600e-6},
                              {'name': 'SENSE', 't' : 75e-3,   'i': 700e-6},
                              {'name': 'SEND',  't' : 7.25e-3,   'i': 1960e-6}], 
                    'skip_initial_task' : 1,
                    'v_on' : 1.9,
                    'v_off' : 1.8,
                    'i_off' : 0, #fully turned off anyway
                    'shutdown_after_completion' : True, #turn yourself off after all tasks are completed
                    'log' : LOG}
    }



# Ideal capacitor model 
capacitor_config = {
    'type' : 'IdealCapacitor',
    'settings': {'capacitance' : 58e-6,
                 'v_rated' : 10,
                 'v_initial' : 2.39,
                 'log' : LOG}
    }

# Original Botoks converter: Hysteresis (MIC841) + LDO
converter_config = {
     'type' : 'LDO',
     'settings' : {'v_out' :  2.2,   
                   'v_high' : 3.1,   #tresholds set using resistors
                   'v_low' :  2.4,   #tresholds set using resistors
                   'i_quiescent' :     4.5e-6, #quiescent current measured using source meter
                   'i_quiescent_off' : 3e-6,   #quiescent current measured using source meter
                   'enable_hyst' : True,
                   'log' : LOG}}


