## Simba tools

This folder contains certain tools that simplify the creation of component modules/configurations.

### IV Curve generator

We provide Python scripts for different sourcemeters to automatically retrieve the IV curve of an energy harvester that can then be directly used with *Simba*'s `IVCurve` module. To this end, connect the harvester to your sourcemeter and use the corresponding script (*get_solar_panel_iv_curve_<SMU_NAME>.py*). The script then instructs the SMU to first obtain the harvester's open-circuit voltage $V_{OC}$ and subsequently measures the current at voltages ranging from $0 ... V_{OC}$ in steps of 50 mV.

- **Keithley 2450**: Install the *Pymeasure* package (`pip install pymeasure`) and use *get_iv_curve_keithley.py* to retrieve the IV curve.
- **Keysight B2900**: Use *get_iv_curve_keysight.py* to retrieve the IV curve.

### TaskLoad configurator

The TaskLoad configurator tool allows to automatically derive a load's list of tasks with their length and power consumption that can be used to configure *Simba*'s `TaskLoad` module. The TaskLoad configurator tool extracts the length and power consumption of the power/GPIO traces, that are obtained using the [nRF Power Profiler 2 Kit](https://www.nordicsemi.com/Products/Development-hardware/Power-Profiler-Kit-2). On the load under test, each active task must be represented on a separate GPIO line that is connected to the nRF PPK2. 

This script uses [IRNAS nRF PPK2 Python library](https://github.com/IRNAS/ppk2-api-python.git). To use the script, download and install the library using:
```
git clone https://github.com/IRNAS/ppk2-api-python.git
cd ppk2-api-python
pip3 install --user .
```

**Recording mode:** To use the TaskLoad configurator in *recording mode* (i.e., the tool directly connects to the PPK and retrieves the traces automatically), choose the PPKs output voltage (default = 3V) and recording time (default = 1s) and run the following command:
```
python get_load_tasks.py -v <VOLTAGE> -t <RECORDING_TIME>
```

**Offline mode:** The TaskLoad configurator can also be used in *offline mode* (i.e., the tool extracts the task list from pre-recorded data). To this end, the data must be exported from the PPK software (press *Save/Export* and *Export*, tick *Timestamp*, *Current*, *Dig. logic pins (single string field)*, and press *Save*).
To use the TaskLoad configurator in *offline mode*, run:
```
python get_load_tasks.py -f <RECORDING_FILE_NAME>
```


Per default, the tasks' names are set to the number of the GPIO line they are indicated on, but can be changed arbitrarily by providing a corresponding map-file (see *task_names.py*).

*Note: The TaskLoad configurator does not work within the DevContainer by default as it requires access to USB. Download and run locally.*
