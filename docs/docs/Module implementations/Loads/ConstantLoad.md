### Description 

The `ConstantLoad` module represents a load that draws a constant current (if any voltage is applied).
### Parameters

| **Parameter** | **man./opt.** | **Value**                | **Description**                                                                                                      |
|---------------|---------------|--------------------------|----------------------------------------------------------------------------------------------------------------------|
|     `current`     |     m         |     Current in A  | Current consumption of load    |
|     `log`     |     o         |    Boolean   | Define whether logging is enabled (Default: `False`)  |

### Example configuration(s)

```
load_config = {
    'type' :  'ConstantLoad',
    'settings' : {'current' : '1e-3'}
    }
```