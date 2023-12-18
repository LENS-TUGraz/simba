### Description 

The `LDO` module describes a converter structure, where a *linear low-dropout regulator* is placed between capacitor and load to convert the capacitor voltage to a fixed output voltage (i.e., `Vout = X`) by dissipating the difference between input/output voltage as waste heat (i.e., `Eout = Vout/Vcap`). In this configuration, there is no converter between harvester and capacitor (i.e., `Vin = Vcap`, `Ein = 1`). 

Additionally, this converter module can optionally model a *hysteresis behavior*, where the output is switched on/off at pre-defined voltage thresholds.
### Parameters

| **Parameter** | **man./opt.** | **Value**                | **Description**                                                                                                      |
|---------------|---------------|--------------------------|----------------------------------------------------------------------------------------------------------------------|
|     `v_out`     |     m         |    Voltage in V   |  Output voltage of LDO   | 
|     `i_quiescent`     |     o         |    Current in A   |  Quiescent current if output enabled (Default: 0)   |
|     `i_quiescent_off`     |     o         |    Voltage in V   | Quiescent current if output disabled (Default: `i_quiescent`)   |
|     `enable_hyst`     |     o         |    Boolean   |  Define whether hysteresis behavior should apply (Default: `False`)  |
|     `v_high`     |     o*         |    Voltage in V   |  Turn-on  hysteresis threshold   |
|     `v_low`     |     o*         |    Voltage in V   |  Turn-off  hysteresis threshold   |
\*Mandatory if `enable_hyst = True` 

### Example configuration(s)

```
converter_config = {
 'type' : 'LDO',
 'settings' : {'v_out' :  2.2,  
			   'v_high' : 3.1,  
			   'v_low' :  2.4,   
			   'enable_hyst' : True,
			   'i_quiescent' :     1e-6}}
```