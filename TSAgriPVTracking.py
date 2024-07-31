from source_py import param_inputs as pi
from source_py.Rhino import rhino_geom

from ladybug.wea import Wea
import ladybug.epw as epw
import numpy as np
import pandas as pd

PARAMS = {}
HOYS = np.arange(0, 8760)
start_date = pd.Timestamp('2023-01-01')
timestamps = [start_date + pd.Timedelta(hours=int(hour)) for hour in HOYS]
TAB_1 = pd.DataFrame()
TAB_1['Month-Day-Hour'] = [ts.strftime('%m-%d-%H') for ts in timestamps]
OUTPUT_PATH = "bdd_irr.xlsx"

def import_STICS_settings():
    df = pi.read_input_excel()
    parameters_excel = pi.transform_df_to_dict(df)
    pi.modify_STICS_files(parameters_excel)
    return parameters_excel

def general_settings():
    print(PARAMS)
    epw_data = epw.EPW(PARAMS['PY_epw_name'])
    PARAMS['PY_wea'] = Wea.from_epw_file(PARAMS['PY_epw_name'], PARAMS['PY_timestep_wea'])
    PARAMS['PY_LARGEUR_AVIDE'] = (PARAMS['PY_RAMPANT']-4*PARAMS['PY_LARGEUR_BANDE'])/3
    PARAMS['PY_NB_PVP_RANGS'] = int(PARAMS['PY_GRID_SIZE'] / PARAMS['PY_ENTRAXE'])
    PARAMS['PY_LONGUEUR_PVP'] = PARAMS['PY_GRID_SIZE'] / (PARAMS['PY_NB_RANGS'])
    PARAMS['PY_LIST_ANGLES'] = np.arange(PARAMS['PY_start_angle'], PARAMS['PY_end_angle'] + 1, PARAMS['PY_PAS_ANGLE'])
    if PARAMS['PY_TYPE_CULT'] == 1 or PARAMS['PY_TYPE_CULT'] == 3:
        PARAMS['PY_HAUTEUR_MESURE'] = 1
    elif PARAMS['PY_TYPE_CULT'] == 2:
        PARAMS['PY_HAUTEUR_MESURE'] = 2.5
    

if __name__ == "__main__":

    #Settings
    PARAMS = import_STICS_settings()
    general_settings()

    #Geom + run irradiance
    rhino_geom.run_annual_irradiance_simulation(angles=PARAMS['PY_LIST_ANGLES'], wea=PARAMS['PY_wea'],tab_1=TAB_1,hoys=HOYS,
                                                output_path=OUTPUT_PATH,FINESSE=PARAMS['PY_FINESSE'],GRID_SIZE=PARAMS['PY_GRID_SIZE'],
                                                ENTRAXE=PARAMS['PY_ENTRAXE'],RAMPANT=PARAMS['PY_RAMPANT'],NB_PVP_RANGS=PARAMS['PY_NB_PVP_RANGS'],
                                                ANGLE_ORIENTATION=PARAMS['PY_ANGLE_ORIENTATION'],TYPE_PANEL=PARAMS['PY_TYPE_PANEL'],
                                                LARGEUR_BANDE=PARAMS['PY_LARGEUR_BANDE'],LARGEUR_AVIDE=PARAMS['PY_LARGEUR_AVIDE'],
                                                LONGUEUR_PVP=PARAMS['PY_LONGUEUR_PVP'],HAUTEUR=PARAMS['PY_HAUTEUR'])
    
    #Excel
    

    print("Fin du main")
