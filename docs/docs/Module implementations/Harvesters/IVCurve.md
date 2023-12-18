### Description 

The `IVCurve` module contains the IV curve of a energy harvester at the certain environmental condition (e.g., for solar panel this means a single IV-curve at a certain brightness). This module thus allows to incorporate the non-linear behavior of many harvesters into the simulation. 

The IV-curves are stored in *Harvesters/harvesting_data/IVCurves* as `.json`-Files. To add new IV-Curves, see *Tools/get_iv_curve_XXXX.py* and the corresponding Readme.
### Parameters

| **Parameter** | **man./opt.** | **Value**                | **Description**                                                                                                      |
|---------------|---------------|--------------------------|----------------------------------------------------------------------------------------------------------------------|
|     `file`     |     m         |     Filename  | Filename of `.json`-File that contains the IV curve data.  |
|     `log`     |     o         |    Boolean   | Define whether logging is enabled (Default: `False`)  |

### Example configuration(s)

```
harvest_config = {  'type'       : 'IVCurve',
					'settings'   : {'file'       : 'KXOB25-02-X8F_lux20000.json',
									'log' : LOG
								    }}
```