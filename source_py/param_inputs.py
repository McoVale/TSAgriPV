import os
import numpy as np
import pandas as pd
import ast

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
r_change_setting = globalenv['change_setting']

def read_input_excel():
    """
    Read an Excel file and return a DataFrame with selected columns.

    This function constructs the path to an Excel file named 'inputs.xlsx' located in the same directory
    as this script, reads the file, and returns a DataFrame containing specific columns and rows.

    Returns:
    pd.DataFrame: A DataFrame containing the selected columns and rows from the Excel file.
    """
    # Get the absolute path of the directory containing this script
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Construct the relative path to the Excel file
    excel_path = os.path.join(script_dir,'..', 'inputs.xlsx')

    # Read the Excel file
    df = pd.read_excel(excel_path, usecols=[1, 2], skiprows=5)
    df.columns = ['Valeur', 'Cle']  

    return df

def transform_df_to_dict(dataframe):
    """
    Transform a DataFrame into a dictionary.

    This function iterates through the rows of the given DataFrame and constructs a dictionary
    where each key is derived from the 'Cle' column and each value is derived from the 'Valeur' column.
    If a value is a string representation of a list, it is converted into an actual list.

    Parameters:
    dataframe (pd.DataFrame): The DataFrame to transform.

    Returns:
    dict: A dictionary with keys and values derived from the DataFrame.
    """
    # Initialize an empty dictionary
    result_dict = {}

    # Iterate through the DataFrame rows and fill the dictionary
    for _, row in dataframe.iterrows():
        key = row['Cle']
        value = row['Valeur']
        
        # If the value is a string representing a list
        if isinstance(value, str) and value.startswith('[') and value.endswith(']'):
            value = ast.literal_eval(value)
        
        result_dict[key] = value
        
    return result_dict

def modify_STICS_files(input_dict):
    """
    Modify STICS XML files based on the provided dictionary.

    This function iterates through a dictionary of parameter names and values, determines the corresponding
    XML file based on the parameter name prefix, and modifies the XML files using the `r_change_setting` function.
    The function uses the `pandas2ri` interface for R and Python integration.

    Parameters:
    input_dict (dict): A dictionary where keys are parameter names and values are the corresponding values to set.

    Returns:
    None
    """
    # For an easy conversion between python and R container types :
    pandas2ri.activate()

    for key, value in input_dict.items():
        if key.startswith('PY_'):
            continue # Skip keys that are not relevant for the STICS setting (python variables)

        # Modify xmlfile depending the prefix    
        if key.startswith("SOILS_"):
            xmlfile = 'sols.xml'
        elif key.startswith("INITS_"):  
            xmlfile = 'VignePioGre_ini.xml'
        elif key.startswith("USMSS_"):
            xmlfile = 'usms.xml'
        elif key.startswith("TECPL_"):
            xmlfile = 'VignePioGre_tec.xml'
        else:
            continue  # Skip keys that don't match known prefixes

        param_name = key[6:]  # Erase prefix

        if isinstance(value, list): # Case the parameter we want to change has more than one value
            # Setting in good form the parameters that will enter the set_param_xml function (see Rfunctions.R)
            value_id = list(range(1, 6))
            value.extend([0] * (5 - len(value)))  # Ensure the list has 5 elements

            r_change_setting(os.path.join('R_related', 'Rproject', xmlfile),
                             param_name=param_name,
                             val=value,
                             values_id=value_id)
        else: # Case the parameter we want to change has a single value
            r_change_setting(os.path.join('R_related', 'Rproject', xmlfile),
                             param_name=param_name,
                             val=value)
    
    pandas2ri.deactivate()

##