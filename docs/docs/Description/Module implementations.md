Module implementations describe the (real-world) hardware components (i.e., harvester, load, converter, or capacitor) and can - for example - contain simple mathematical representations of (ideal) components, complex analytical models, or  data sets from experimental campaigns.
To define and use a certain module implementation, the module-specific [[Module implementations#Module interfaces\|interfaces]] have to be implemented and the desired module has to be [[Module implementations#Configuration\|configured]] accordingly.

## Available module implementations

*Simba* provides a number of pre-defined module implementations which can be configured individually and thus already cover a large number of different battery-free systems.

| **Module**       | **ModuleTypes**       |
|------------------|--------------------------|
| Harvesters | [[Artificial]], [[IVCurve]], [[SolarPanel]], [[TEG]]  |
| Converter  | [[Diode (converter-less)]], [[BuckBoost]], [[LDO]], [[BQ25570]]       | 
| Capacitor  | [[IdealCapacitor]], [[TantulumCapacitor]]| 
| Load       | [[ConstantLoad]], [[TaskLoad]], [[JITLoad]], [[JITLoadAdvanced]] | 

## Configuration

To select the desired module implementation, each module (i.e., Harvester, Converter, Capacitor etc.) can be configured using a dedicated configuration (file) in `.json` format as follows:

```
{
  "type": "<ModuleType>",
  "settings" : "<ModuleSettings>"
}
```

*<ModuleType\>* is the name of the subtype/implementation of the module and *<ModuleSettings\>*  contain module-specific settings. For module-specific settings, check out the description of each module implementation.

## Module interfaces

In order to create a new *Simba*-compatible module implementation, a number of methods have to implemented accordingly. This include *common methods* that are called for all modules (e.g., `reset`, `update_state` etc.) and *module-specific methods* that are only required for a certain type of module (e.g., `get_input_efficiency` is certainly only required for the converter module).

In the following, we briefly describe the mandatory common and module-specific methods for each module type.
### Common methods

- `reset()`: Initialize the module (e.g., load required data, set up variables) and set initial state.
- `update_state()`: Update the module's internal state and log data if required - for more module-specific information, see below.
- `process_log()`: Called at the end of the simulation to process logging data from module implementation (if required).
- `get_log()`: Retrieve (detailed) logging data from module implementation as [Pandas](https://pandas.pydata.org/) `DataFrame` datatype.
- `get_stats()`: Derive module-specific statistics from logging data and provide this data as a `dict` data type (for more details, refer to [[Trade-off exploration]]).
- `get_next_change()`: Inform the simulation core of the next expected update within the module (i.e., returns the time until next update in seconds)  - for more module-specific information, see below.
### Harvester-specific methods

The `Harvester` modules represent energy sources that supply the sensor node with incoming power.

*Common methods*

- `update_state(time, dt, v_in)`: Update state if necessary (i.e., if environmental conditions have changed and a different harvesting current applies) and log (actual and maximal) harvesting current and applied voltage at given time.
- `get_next_change(time)`: Inform the simulation core when the harvesting conditions change.

*Harvester-specific methods (mandatory)*

- `get_current(time, v_in)`: Return the harvesting current (in A) at the specified voltage at the current time.
- `get_ocv(time)`: Return open-circuit voltage of harvester at the current time.

*Harvester-specific methods (optional)*

- `plot_iv_curve()`, `plot_irradiance()`, `...` : Harvester-specific plot functions to support users while using *Simba*.

### Converter-specific methods
The `Converter` modules represent the voltage converter(s) between harvester and capacitors ("`input`") as well as capacitor and load ("`output`").

*Common methods*

- `update_state(time, dt, cap_voltage)`: Update state if necessary (i.e., turn-on/turn-off thresholds have been reached) and log converter-specific values (e.g., efficiencies, quiescent current, state) at given time.
- `get_next_change(time)`: Inform the simulation core when the converter changes its state (e.g., when the next MPP sampling takes place).

*Converter-specific methods (mandatory)*

- `get_input_operating_voltage(v_cap)`: Return (operating) voltage of converter between harvester and capacitor.
- `get_input_efficiency(v_cap, i_in)`: Return efficiency of converter between  harvester and capacitor.
- `get_output_operating_voltage(v_cap)`: Return output voltage of converter between capacitor and load.
- `get_output_efficiency(v_cap, i_out)`: Return efficiency of converter between capacitor and load.
- `get_quiescent(v_cap)`: Return quiescent current (in A) depending on voltage level.
- `get_next_threshold(v_cap, i_total)`: If any, return the next voltage threshold at which the converter will change its state.

### Capacitor-specific methods

The `Capacitor` modules describe the energy buffer between harvester and load.

*Common methods*

- `update_state(time, dt, i_total)`: Update the capacitor's state (i.e., state of charge) according to the current flow and the capacitor's leakage and log capacitor voltage (and leakage) at the given time.
- `get_next_change(i_total, voltage_threshold)`: Inform the simulation core when the given voltage threshold (e.g., supplied by the load or converter) would be reached, given the actual current.

*Capacitor-specific methods (mandatory)*

- `get_voltage()`: Provide the current voltage of the capacitor.

### Load-specific methods

The `Load` modules represent the load (e.g., sensor node) to be powered by the harvester and capacitor. Note that the load module must include/model the power consumption of both the MCU and any peripherals attached to it.

*Common methods*

- `update_state(time, dt, v_out, v_cap)`: Update the load's internal state (e.g., currently running task etc.) accordingly and log any load-specific values (e.g., state, voltages, current consumption) at the given time.
- `get_next_change(time)`: Inform the simulation core when the load changes its state (e.g., when the next task is scheduled).
- `get_next_threshold(v_cap, i_total)`: If any, return the next voltage threshold at which the load will change its state.

*Load-specific methods (mandatory)*

- `get_current(v_out)`: Return the load's current consumption in the current state.
- `get_state()`: Return the load's current internal state (for logging purposes only).
