### NREL solar irradiance traces

This folder contains data solar irradiance traces from *outdoor environments* that are obtained by the NREL Solar Radiation Research Laboratory at the Baseline Measurement System in Golden, Colorado.

The *raw* traces include 1-minute data of solar irradiance in W/m^2 measured with a CM3 pyranometer. For detailed information, see: http://dx.doi.org/10.5439/1052221

To download additional traces (from the same location)
- Go to https://midcdmz.nrel.gov/apps/sitehome.pl?site=BMS
- Click 'Daily plots and raw data files'
- Choose your desired time frame
- In the upcoming page:
    - select start/end date
    - tick 'Global CM3 (corr.)'
    - select 'Select 1-Min Data (ASCII Text)' (*or any resolution that is desired*)
    - press 'Submit'
- Store the loaded data as *.txt*-file
- Run `python3 process_solar_harvest_data.py` to convert the data to be compatible with *Simba*'s `SolarPanel` module
