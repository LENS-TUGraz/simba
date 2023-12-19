### Description 

The `SolarPanel` module allows to use long-term real-world solar energy harvesting traces in simulation, by including
- a [PV cell model](https://www.mdpi.com/1996-1073/9/5/326) that can be configured according to parameters that are typically available in datasheets, and
- real-world solar irradiance traces from existing datasets (e.g., [NREL](https://midcdmz.nrel.gov/apps/sitehome.pl?site=BMS) for outdoor and [ENHANTS](https://enhants.ee.columbia.edu/indoor-irradiance-meas) for indoor environments).

Examples for solar irradiance traces and their format can be found in *Harvesters/harvesting_data/SolarTraces/DATASET*. They can be extended with additional custom traces or with traces downloaded from the mentioned datasets (see Readmes in the corresponding folders).

### Parameters

| **Parameter** | **man./opt.** | **Value**                | **Description**                                                                                                      |
|---------------|---------------|--------------------------|----------------------------------------------------------------------------------------------------------------------|
|     `file`     |     m         |     Filename  | Filename of `.json`-File that contains the solar irradiation trace (e.g., *DATASET/trace.json*)  |
|     `t_start`     |     o         |     Time in seconds  | Start time of harvesting trace for simulation (to cut beginning of full trace) (Default: 0) |
|     `t_max`     |    o         |     Time in seconds  | Total time of harvesting trace for simulation (to cut end of full trace and limit amount of stored data during simulation) (Default: max. trace length) |
|     `i_sc`     |     m         |    Current in A   | Short circuit current of solar panel (or single cell) at 1000 W/m2 |
|     `v_oc`     |     m         |    Voltage in V   | Open circuit voltage of solar panel (or single cell) at 1000 W/m2 |
|     `i_mpp`     |     m         |    Current in A | Current at MPP at 1000 W/m2 |
|     `v_mpp`     |     m         |    Voltage in V  | Voltage at MPP at 1000 W/m2 |
|     `num_cells`     |     o         | Integer   | Number of PV cells in solar panel (Default: 1)  |
|     `connection`     |     o*         |    "parallel" or "series"   | Define how the PV cells are connected |
|     `log`     |     o         |    Boolean   | Define whether logging is enabled (Default: `False`)  |

\* mandatory if `num_cells > 1` 
### Example configuration(s)

```
harvest_config = {'type'       : 'SolarPanel',
                  'settings'   : {'file'       : 'NREL/2023jun.json',
                                  'i_sc' : 14.8e-3,
                                  'v_oc' : 3.56,
                                  'v_mpp': 2.6,
                                  'i_mpp': 12.1e-3,
                                  'log' : True
                                  }}

harvest_config = {'type'       : 'SolarPanel',
                  'settings'   : {'file'       : 'NREL/2023jun.json',
                                  'i_sc' : 14.8e-3,
                                  'v_oc' : 3.56,
                                  'v_mpp': 2.6,
                                  'i_mpp': 12.1e-3,
                                  'num_cells' : 2,
                                  'connection' : 'parallel'
                                  'log' : True
                                  }}

```