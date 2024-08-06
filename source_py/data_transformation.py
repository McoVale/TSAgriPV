import pandas as pd
import numpy as np
from source_py.scenario import Scenario
import os

def import_scenario():
    """
    Imports a scenario from an Excel file and returns a Scenario object.

    The Excel file used is located at "DATA/sc.xlsx". This file should contain
    the necessary data to create a Scenario instance.

    Returns:
        Scenario: A Scenario object created from the data in the Excel file.
    """
    return Scenario(file_path="DATA/scenario.xlsx")
    
def import_bdd_irr(input_path):
    """
    Imports irradiance data from an Excel file and returns it as a DataFrame.

    Args:
        input_path (str): Path to the Excel file containing the irradiance data.

    Returns:
        pd.DataFrame: A DataFrame with irradiance data loaded from the specified Excel file.
    """
    return pd.read_excel(input_path)

def import_pvsyst_file():
    """
    Imports PVSYST files from an Excel workbook and returns a DataFrame with the 'Illim' sheet.

    The Excel workbook is located at "DATA/pvsyst_file.xlsm". This function reads the 'Illim' sheet, processes it by dropping
    unnecessary rows and columns, and returns the cleaned DataFrame.

    Returns:
        pd.DataFrame: A DataFrame with the 'Illim' sheet from the PVSYST Excel file.
    """
    pvsyst = pd.read_excel("DATA/pvsyst_file.xlsm", sheet_name=['Tests','Illim'])
    pvsyst_illim = pvsyst['Illim'].drop(index=list(range(12))).drop(columns=['Unnamed: 4', 'Unnamed: 5']).reset_index(drop=True)
    pvsyst_illim.columns = ['Date','E_Grid','PR','PhiAng']
    return pvsyst_illim

def creer_tab_effacement(sc, bdd_irr, pvsyst, step_angle, data_name):
    """
    Creates a DataFrame with columns updated based on various shading scenarios.

    Args:
        sc: Shading scenario object.
        bdd_irr: Ground irradiance database for each angle imported.
        pvsyst: PVSYST data, 'Illim' sheet, imported.
        step_angle: Angle step used for the light simulation.

    Returns:
        tab_eff: Updated DataFrame with 'effacement', 'angle', 'irradiance_sol', and 'temoin' columns.
    """
    # Initialize the DataFrame tab_eff
    tab_eff = pd.DataFrame(columns=['hoys', 'effacement', 'angle', 'irradiance_sol', 'temoin'])
    tab_eff['hoys'] = bdd_irr['Month-Day-Hour']  # Ensure the 'hoys' column matches the 'Month-Day-Hour' column in bdd_irr
    tab_eff['effacement'] = 1  # Default initialization to 1
    
    # Filling the 'effacement' column
    for i in range(sc.scenario.shape[0]):  # For each row
        for j in range(sc.scenario.shape[1]):  # For each column
            if sc.scenario[i, j] == False:
                tab_eff.loc[(tab_eff['hoys'].str.slice(6, 8) == f'{j:02d}') & (tab_eff['hoys'].str.slice(0, 2) == f'{i + 1:02d}'), 'effacement'] = 0

    # Filling the 'angle' and 'irradiance_sol' columns
    for i in range(tab_eff.shape[0]):
        if tab_eff.at[i, 'effacement'] == 0:
            tab_eff.loc[i, 'irradiance_sol'] = bdd_irr.drop(columns=['Month-Day-Hour', 'temoin']).iloc[i].max()  # Maximum irradiance
            tab_eff.loc[i, 'angle'] = bdd_irr.drop(columns=['Month-Day-Hour', 'temoin']).iloc[i].idxmax()  # Column with maximum irradiance
        else:  # 'effacement' == 1
            angle_rounded = round(pvsyst.loc[i, 'PhiAng'] / step_angle) * step_angle
            tab_eff.loc[i, 'irradiance_sol'] = bdd_irr.at[i, str(angle_rounded)]
            tab_eff.loc[i, 'angle'] = angle_rounded

    # Add control values to tab_eff
    tab_eff['temoin'] = bdd_irr['temoin']
    
    tab_eff.to_excel("DATA/"+data_name+"/tab_effacement_"+data_name+".xlsx", index=False, header=True)

    return None

def creer_daily_ratios(data_name):
    """
    Creates daily ratios from the efficiency DataFrame and saves them to CSV files.

    Args:
        tab_eff1: DataFrame containing efficiency data, including columns 'hoys', 'irradiance_sol', and 'temoin'.
        data_name: String used to name the output CSV files.

    Returns:
        None: The function saves the calculated daily ratios to CSV files.
    """

    tab_eff1 = pd.read_excel("DATA/"+data_name+"/tab_effacement_"+data_name+".xlsx")
    # Extract the date from the 'hoys' column
    tab_eff1['Date'] = tab_eff1['hoys'].str[:5]
   
    # Aggregate daily by summing the 'irradiance_sol' and 'temoin' columns
    daily_sum = tab_eff1.groupby('Date')[['irradiance_sol', 'temoin']].sum().reset_index()

    # Calculate the daily ratios, ensuring no division by zero
    daily_sum['ratio'] = daily_sum.apply(lambda row: row['irradiance_sol'] / row['temoin'] if row['temoin'] != 0 else float('inf'), axis=1)
    
    # Apply a lambda function to ensure ratios do not exceed 1
    daily_sum['ratio'] = daily_sum['ratio'].apply(lambda x: min(x, 1))

    # Save the daily ratios to CSV files 
    daily_sum['ratio'].to_csv("DATA/"+data_name+"/ratios_" + data_name + ".csv", index=False, header=False)
    
    return None

##