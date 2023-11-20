# Configuration(s) for simulation

LOG = False

#Solar harvesting
harvest_config_solar = {'type'       : 'IVCurve',
                        'settings'   : {'file'       : 'Gameboy_luxXXXXX.json',
                                        'lux' : 13000,
                                        'log' : LOG
                                     }}

harvest_config_solar_long = {'type'       : 'SolarPanel',
                            'settings'   : {'data_type'  : 'Irradiance',
                                           'file'       : '2023jun.json',
                                           'i_sc' : 14.8e-3,
                                           'v_oc' : 3.56,
                                           'v_mpp': 2.6,
                                           'i_mpp': 12.1e-3, 
                                           'log' : True
                                           }}
harvest_config_const = {
    'type' :  'Artificial',
    'settings' : {'shape' : 'const',
                  'i_high' : 3.5e-3,
                  'v_oc' : 3}
    }

load_config = {
    'type' : 'JITLoad',
    'name' : 'Gameboy',
    'settings' : {  'currents' : {   'RESTORE' : 2.65e-3*0.97,
                                     'COMPUTE' : 3.28e-3*0.97,
                                     'CHECKPOINT' : 2.87e-3*0.97},
                    't_checkpoint' : 33e-3,
                    't_checkpoint_period' : 270e-3,
                    't_restore' : 255e-3,
                    't_restore_startup' : 255e-3,
                    'v_on' : 2.9,
                    'v_off' : 2.8,
                    'v_checkpoint' : 3.4,
                    'log' : True}
    }


# Ideal capacitor model 
capacitor_config = {
    'type' : 'IdealCapacitor',
    'settings': {'capacitance' : 3300e-6,
                'v_rated' : 10,
                'v_initial' : 3.0,
                'log' : LOG}
    }


converter_config = {
    'type' : 'BQ25570',
    'settings' : {'v_ov' : 4.98,
                  'v_out' : 3.0,
                  'vout_ok_high' : 3.97,
                  'vout_ok_low' : 3.32,
                  'vout_ok_enable' : True,
                  'mpp' : 0.8,
                  'log' : True
                  }}

# Real, measured values of C and V_high
cap_values = {1000 : 1115e-6, 
              3300 : 3910e-6,
              6800 : 7100e-6}

v_high_values = {3.6 : 3.67,
                 4.0 : 4.0,
                 4.3 : 4.33}

color_map = {'RESTORE' : 'blue',
             'COMPUTE' : 'green',
             'CHECKPOINT' : 'orange',
             'OFF' : 'white'}