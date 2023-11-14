## Simba tools

This folder contains certain tools that simplify the creation of component modules/configurations.

### IV Curve generator

We provide Python scripts for different sourcemeters to automatically retrieve the IV curve of an energy harvester that can then be directly used with *Simba*'s `IVCurve` module. To this end, connect the harvester to your sourcemeter and use the corresponding script (*get_solar_panel_iv_curve_<SMU_NAME>.py*). The script then instructs the SMU to first obtain the harvester's open-circuit voltage $V_{OC}$ and subsequently measures the current at voltages ranging from $0 ... V_{OC}$ in steps of 50 mV.

- **Keithley 2450**: Install the *Pymeasure* package (`pip install pymeasure`) and use *get_solar_panel_iv_curve_keithley.py* to retrieve the IV curve.
- **Keysight B2900**: TODO

