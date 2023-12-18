### Description 

The `TantulumCapacitor` module describes a capacitor of the AVX TAJ series with a certain capacitance and voltage ratings. In contrast to an ideal capacitor, tantulum capacitors exhibit leakage currents that depend on (i) the capacitance, (ii) the rated voltage, and (iii) the applied voltage. This behavior is modelled according to the AVX technical notes and accounted for in the charge/discharge behavior of the capacitor.

For more details on the leakage modeling, see: 

- *Low Leakage Current Aspect of Designing with  Tantalum and Niobium Oxide Capacitors*: https://www.avx.com/docs/techinfo/Low_Leakage_Current_Aspect_Designing_Tantalum_Niobium_Oxide_Capacitors.pdf).
- Jie Zhan et al. *Exploring the Effect of Energy Storage Sizing on Intermittent
Computing System Performance*. IEEE Trans. on Computer-Aided Design of
Integrated Circuits and Systems (2022).

### Parameters

| **Parameter**       | **man./opt.** | **Value**                      | **Description**                              |
|---------------------|---------------|--------------------------------|----------------------------------------------|
|     `capacitance`   |     m         |     Capacitance in F           |                                              |
|     `v_rated`       |     m         |     Max. rated voltage in V    |     To log ‘overvoltage’ alarm               |
|     `v_initial`     |     o         |     Voltage in V               |     Voltage at start of sim. (Default: 0)    |

### Example configuration(s)

```
cap_config = {
    'type' :  'Tantulum',
    'settings' : {'capacitance' : 10e-6,
                  'v_rated' : 10,
                  'v_initial' : 3.3}
    }
```