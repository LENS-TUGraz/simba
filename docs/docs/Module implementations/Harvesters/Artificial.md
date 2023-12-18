### Description 

The `Artificial` energy source can supply current either constantly or as a sine/square wave (more waveforms can be implemented on demand) with adjustable current amplitude and duty cycle.
### Parameters

| **Parameter** | **man./opt.** | **Value**                | **Description**                                                                                                      |
|---------------|---------------|--------------------------|----------------------------------------------------------------------------------------------------------------------|
|     `shape`     |     m         |     `const`, `square`, `sine`  | Either constant current, square wave (repeating i_high for t_high and t_high for t_low), or sine wave (with a period of period and an amplitude between 0 and i_high)    |
|     `i_high`    |     m         |     Current in A         |  Constant current value (`const`), value of high phase (`square`), amplitude (`sine`)                                                  |
|     `i_low`     |     m\*        |     Current in A         | Value of low phase (`square` only)                                                                               |
|     `t_high`    |     m\*        |     Time in seconds      |  Length of high phase (`square` only)                                                                                      |
|     `t_low`     |     m\*        |     Time in seconds      | Length of low phase (`square` only)    
| `period` | m** | Time in seconds |  Period of sine wave (`sine` only)  | 
|     `log`     |     o         |    Boolean   | Define whether logging is enabled (Default: `False`)  |

\*Mandatory for `square` shape \** Mandatory for `sine` shape
### Example configuration(s)

```
harvest_config_const = {
    'type' :  'Artificial',
    'settings' : {'shape' : 'const',
                  'i_high' : 400e-6}
    }
    
harvest_config_square = {
    'type' :  'Artificial',
    'settings' : {'shape' : 'square',
                  'i_high' : 400e-6,
                  'i_low' : 0,
                  't_high' : 100e-6,
                  't_low' : 100e-6}
    }
    
harvest_config_sine = {
    'type' :  'Artificial',
    'settings' : {'shape' : 'sine',
                  'i_high' : 400e-6,
                  'period' : 100e-3}
    }
```