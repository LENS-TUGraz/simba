### Description 

The `Diode` module describes an (ideal) converter-less node architecture where energy harvester, capacitor, and load are *directly coupled* (i.e., `Vin = Vcap` and `Vout = Vcap`). Typically, a diode is used in this settings to avoid a backfeeding of the capacitor's energy to the harvester. Note that in this model, no diode voltage drop is considered.
This model also implements an overvoltage protection of the capacitor, i.e., the input efficiency is set to 0 if `Vcap` > `v_ov`. Otherwise, the input/output efficiencies are set to 100% and no losses are considered (`Ein = Eout = 1`, `i_quiescent = 0`).
### Parameters

| **Parameter** | **man./opt.** | **Value**                | **Description**                                                                                                      |
|---------------|---------------|--------------------------|----------------------------------------------------------------------------------------------------------------------|
|     `v_ov`     |     m         |    Voltage in V   |  Overvoltage protection   |                                                                          |

### Example configuration(s)

```
converter_config = {
    'type' : 'Diode',
    'settings' : {'v_ov' : 3.3}
    }
```