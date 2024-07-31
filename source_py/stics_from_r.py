import pandas as pd
import numpy as np
import os.path

####------------------------
####--R localization setup--
####------------------------
def find_r_installation():
    possible_paths = []

    # Add standard paths for Windows
    if os.getenv('ProgramFiles'):
        possible_paths.append(os.path.join(os.getenv('ProgramFiles'), 'R'))
    if os.getenv('ProgramFiles(x86)'):
        possible_paths.append(os.path.join(os.getenv('ProgramFiles(x86)'), 'R'))
    if os.getenv('LOCALAPPDATA'):
        possible_paths.append(os.path.join(os.getenv('LOCALAPPDATA'), 'Programs', 'R'))
    
    # Add standard path for Unix-like systems <- optionnal ?
    if os.getenv('HOME'):
        possible_paths.append(os.path.join(os.getenv('HOME'), 'R'))

    for path in possible_paths:
        if os.path.exists(path):
            for root, dirs, files in os.walk(path):
                if 'bin' in dirs:
                    if 'R.exe' in os.listdir(os.path.join(root, 'bin')):  # Check specifically for Windows
                        return os.path.join(root)
                    if 'R' in os.listdir(os.path.join(root, 'bin')):  # Check for Unix-like systems
                        return os.path.join(root)

    return None

r_path = find_r_installation()
if r_path:
    print(f"R is installed at: {r_path}")
else:
    print("R installation not found.")

os.environ['R_HOME'] = r_path
####------------------------
####------------------------
####------------------------

###Imports RPY2
from rpy2.robjects import pandas2ri
from rpy2.robjects import r
from rpy2.robjects import globalenv

###Imports inside R
r.source("R_related/Rfunctions.R")
f_copy_weather_files = globalenv['copy_weather_files']
f_run_simulation = globalenv['run_simulation']
f_change_scenar = globalenv['change_scenar']

def gen_weatherfile_from_epw(epw_file_path, start_date):
    """
    Read an EPW file to create and export weather data files.

    Args:
        epw_file_path (str): Path to the EPW file.
        output_dir (str): Directory to save the processed weather files.
        start_date (str): Start date for the date range (format 'YYYY-MM-DD').
        end_date (str): End date for the date range (format 'YYYY-MM-DD').

    Returns:
        None
    """
    # Read the EPW file, skipping the first 8 metadata rows
    epw_data = pd.read_csv(epw_file_path, skiprows=8, header=None)
    
    # Create the weatherFile DataFrame with basic columns
    date_range = pd.date_range(start=start_date, end=(start_date + pd.DateOffset(years=1, days = -1)))
    weatherFile = pd.DataFrame({
        'file': ['weatherFile_TEST'] * len(date_range),
        'year': [date_range.year[0]] * len(date_range),
        'month': date_range.month,
        'day': date_range.day,
        'doy': date_range.dayofyear
    })
    
    # Initialize additional columns
    weatherFile['temp_min'] = np.nan
    weatherFile['temp_max'] = np.nan
    weatherFile['Radiation'] = np.nan
    weatherFile['Etp'] = -999.9
    weatherFile['Rain'] = np.nan
    weatherFile['Wind'] = np.nan
    weatherFile['Tpm'] = -999.9
    weatherFile['Co2'] = 412
    
    # Calculate daily values for each column
    for i, date in enumerate(date_range):
        start_hour = i * 24
        end_hour = start_hour + 24
        
        daily_data = epw_data.iloc[start_hour:end_hour]
        
        weatherFile.at[i, 'temp_min'] = daily_data[6].min()  # Column G
        weatherFile.at[i, 'temp_max'] = daily_data[6].max()  # Column G
        weatherFile.at[i, 'Radiation'] = daily_data[13].sum() * 0.0036  # Column N, convert Wh/m2 to MJ/m2
        weatherFile.at[i, 'Rain'] = daily_data[33].sum()  # Column AH
        weatherFile.at[i, 'Wind'] = daily_data[21].mean()  # Column V
    
    weatherFile = weatherFile.round(2)
    
    # Display the first few rows of the DataFrame for verification
    # print(weatherFile.head())
    
    # Export the DataFrame to CSV files (weatherFile)
    weatherFile.to_csv('R_related/weatherFilesSource/weatherFile_TEST.'+str(start_date.year),
                       sep=' ', index=False, header = False)
    
    # Create and export the second weatherFile (same, but the year is the next one)
    weatherFile2 = weatherFile.copy()
    weatherFile2['year'] = (start_date + pd.DateOffset(years=1)).year
    weatherFile2.to_csv('R_related/weatherFilesSource/weatherFile_TEST.'+str(start_date.year+1),
                        sep=' ', index=False, header = False)
    return None

def stics_simulation(source_dir, workspace_path, javastics_path, usm_name, data_name):
    """
    Run STICS simulations by calling R functions from an R script using rpy2.

    Args:
        source_dir (str): Directory containing the source weather files.
        workspace_path (str): Working directory for the simulation.
        javastics_path (str): Path to the JavaStics executable.
        usm (str): USM (Simulation Management Unit) name.
        results_path (str): Path to the results CSV file.
        irradiance_params_path (str): Path to the CSV file containing irradiance parameters.

    Returns:
        tuple: PdsFruitFrais values from the two simulations.
    """
    pandas2ri.activate()

    # Copy weather files
    f_copy_weather_files(source_dir, workspace_path)
    
    # Run the first simulation
    f_run_simulation(javastics_path, workspace_path, usm_name)

    # Get the first simulation results
    # Read the CSV file
    results_simu = pd.read_csv("R_related/Rproject/mod_s"+usm_name+".sti", sep=";")
    pdsfruitfraisSim1 = results_simu['pdsfruitfrais'].max()

    # Change weather file
    f_change_scenar(data_name)

    # Run the second simulation
    f_run_simulation(javastics_path, workspace_path, usm_name)

    # Get the second simulation results
    # Read the CSV file
    results_simu2 = pd.read_csv("R_related/Rproject/mod_s"+usm_name+".sti", sep=";")
    pdsfruitfraisSim2 = results_simu2['pdsfruitfrais'].max()

    pandas2ri.deactivate()

    return pdsfruitfraisSim1,pdsfruitfraisSim2
##