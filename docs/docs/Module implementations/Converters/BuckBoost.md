### Description 

The `BuckBoost` module describes a converter structure, where the boost- and buck-converter stages can be configured arbitrarily. For both converters, the voltage and efficiencies can be set accordingly. If the input/output voltage is not configured or set to zero, it is assumed that no converter is used (e.g., `Vout = Vcap` + `Eout = 1` or `Vin = Vcap`+ `Ein = 1`).

This model also implements an overvoltage protection of the capacitor, i.e., the input efficiency is set to 0 if `VCap` > `v_ov`, and the quiescent current of the converter(s) can be configured.

### Parameters

| **Parameter** | **man./opt.** | **Value**                | **Description**                                                                                                      |
|---------------|---------------|--------------------------|----------------------------------------------------------------------------------------------------------------------|
|     `v_out`     |     o         |    Voltage in V   |  Output voltage of buck converter (if `v_out > 0`, else `Vout = VCap`) (Default: 0)  | 
|     `v_in`     |     o         |     Voltage in V   |  Output voltage of boost converter (if `v_in > 0`, else `Vin = VCap`) (Default: 0)|
|     `efficiency_out`     |     o         |    (0 ... 1)   | Efficiency of buck converter (Default: 1) |
|     `efficiency_in`     |     o         |    (0 ... 1)  |  Efficiency of boost converter  (Default: 1)  |
|     `v_ov`     |     m         |    Voltage in V   |  Over-voltage threshold |
|     `i_quiescent`     |     o         |    Current in A   |  Quiescent current of converter (Default: 0)  |

### Example configuration(s)

```
config_buck_only = {
	 'type' : 'BuckBoost',
	 'settings' : {'v_out' : 2.0,  
				   'v_in' : 0,  # or omit entirely, v_in is set to v_cap
				   'efficiency_out' :  0.8,   
				   'efficiency_in' : 1, # or omit entirely, Ein is set to 1
				   'v_ov' : 5.0,
				   'i_quiescent' : 1e-6}},
			   
config_boost_only = {
	 'type' : 'BuckBoost',
	 'settings' : {'v_out' : 0,  # or omit entirely, v_out is set to v_cap
				   'v_in' : 1.5, 
				   'efficiency_out' : 1, # or omit entirely, Eout is set to 1
				   'efficiency_in' : 0.6,   
				   'v_ov' : 5.0,
				   'i_quiescent' : 1e-6}},

config_buck_boost = {
	 'type' : 'BuckBoost',
	 'settings' : {'v_out' : 2.0,  
				   'v_in' : 1.5, 
				   'efficiency_out' : 0.8,
				   'efficiency_in' : 0.6,   
				   'v_ov' : 5.0,
				   'i_quiescent' : 1e-6}},

```