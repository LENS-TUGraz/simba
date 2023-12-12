### Description 

The `IdealCapacitor` module describes an ideal capacitor (i.e., with no leakage) with a certain capacitance and voltage rating.
### Parameters

| **Parameter**       | **man./opt.** | **Value**                      | **Description**                              |
|---------------------|---------------|--------------------------------|----------------------------------------------|
|     `capacitance`   |     m         |     Capacitance in F           |                                              |
|     `v_rated`       |     m         |     Max. rated voltage in V    |     To log ‘overvoltage’ alarm               |
|     `v_initial`     |     o         |     Voltage in V               |     Voltage at start of sim. (Default: 0)    |

### Example configuration(s)

```
cap_config = {
    'type' :  'Ideal',
    'settings' : {'capacitance' : 10e-6,
                  'v_rated' : 10}
    }
```