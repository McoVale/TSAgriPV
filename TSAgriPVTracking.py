from source_py import param_inputs as pi
from source_py.Rhino import rhino_geom
from source_py import data_transformation as dt
from source_py import stics_from_r as stics

from ladybug.wea import Wea
import numpy as np
import pandas as pd

PARAMS = {}
HOYS = np.arange(0, 8760)
START_DATE = pd.Timestamp('2022-01-01')
timestamps = [START_DATE + pd.Timedelta(hours=int(hour)) for hour in HOYS]
TAB_1 = pd.DataFrame()
TAB_1['Month-Day-Hour'] = [ts.strftime('%m-%d-%H') for ts in timestamps]
JAVASTICS_PATH = 'JavaSTICS/'
R_STICS_WORKSPACE = 'R_related/Rproject/'

def import_STICS_settings():
    df = pi.read_input_excel()
    parameters_excel = pi.transform_df_to_dict(df)
    pi.modify_STICS_files(parameters_excel)
    return parameters_excel

def general_settings():
    PARAMS['PY_TYPE_PANEL'] = bool(PARAMS['PY_TYPE_PANEL'])
    PARAMS['PY_DO_RHINO_SIM'] = bool(PARAMS['PY_DO_RHINO_SIM'])
    PARAMS['PY_wea'] = Wea.from_epw_file(PARAMS['PY_epw_name'], PARAMS['PY_timestep_wea'])
    PARAMS['PY_LARGEUR_AVIDE'] = (PARAMS['PY_RAMPANT']-4*PARAMS['PY_LARGEUR_BANDE'])/3
    PARAMS['PY_NB_PVP_RANGS'] = int(PARAMS['PY_GRID_SIZE'] / PARAMS['PY_ENTRAXE'])
    PARAMS['PY_LONGUEUR_PVP'] = PARAMS['PY_GRID_SIZE'] / (PARAMS['PY_NB_RANGS'])
    PARAMS['PY_LIST_ANGLES'] = np.arange(PARAMS['PY_start_angle'], PARAMS['PY_end_angle'] + 1, PARAMS['PY_PAS_ANGLE'])
    if PARAMS['PY_TYPE_CULT'] == 1 or PARAMS['PY_TYPE_CULT'] == 3:
        PARAMS['PY_HAUTEUR_MESURE'] = 1
    elif PARAMS['PY_TYPE_CULT'] == 2:
        PARAMS['PY_HAUTEUR_MESURE'] = 2.5
    PARAMS['PY_PATH_BDD_IRR'] = 'DATA/bdd_irr_'+PARAMS['PY_DATA_NAME']+'.xlsx'
    return True

def run_data_transformation():
    scenar = dt.import_scenario()
    bdd_irrad = dt.import_bdd_irr(PARAMS['PY_PATH_BDD_IRR'])
    pvsyst_file = dt.import_pvsyst_file()
    dt.creer_tab_effacement(sc=scenar, bdd_irr=bdd_irrad,
                                      pvsyst=pvsyst_file, step_angle= PARAMS['PY_PAS_ANGLE'],
                                      data_name=PARAMS['PY_DATA_NAME'])
    dt.creer_daily_ratios(data_name=PARAMS['PY_DATA_NAME'])
    return True

def run_stics_simu():
    stics.gen_weatherfile_from_epw(PARAMS['PY_epw_name'],START_DATE)
    res1 = stics.stics_simulation(source_dir="R_related/weatherFilesSource/", workspace_path=R_STICS_WORKSPACE,
                           javastics_path= JAVASTICS_PATH, usm_name=PARAMS['PY_USM_NAME'],
                           data_name=PARAMS['PY_DATA_NAME'])
    print("récoltes ",res1," t/ha")
    return True

if __name__ == "__main__":

    # Settings
    PARAMS = import_STICS_settings()
    print(PARAMS)
    general_settings()

    # Run Geom + Irradiance if wanted (PY_RHINO_SIM == TRUE)
    # print(PARAMS['PY_DO_RHINO_SIM'])
    if PARAMS['PY_DO_RHINO_SIM'] == True :
        rhino_geom.run_annual_irradiance_simulation(angles=PARAMS['PY_LIST_ANGLES'], wea=PARAMS['PY_wea'],tab_1=TAB_1,hoys=HOYS,
                                                    output_path=PARAMS['PY_PATH_BDD_IRR'],FINESSE=PARAMS['PY_FINESSE'],GRID_SIZE=PARAMS['PY_GRID_SIZE'],
                                                    ENTRAXE=PARAMS['PY_ENTRAXE'],RAMPANT=PARAMS['PY_RAMPANT'],NB_PVP_RANGS=PARAMS['PY_NB_PVP_RANGS'],
                                                    ANGLE_ORIENTATION=PARAMS['PY_ANGLE_ORIENTATION'],TYPE_PANEL=PARAMS['PY_TYPE_PANEL'],
                                                    LARGEUR_BANDE=PARAMS['PY_LARGEUR_BANDE'],LARGEUR_AVIDE=PARAMS['PY_LARGEUR_AVIDE'],
                                                    LONGUEUR_PVP=PARAMS['PY_LONGUEUR_PVP'],HAUTEUR=PARAMS['PY_HAUTEUR'])
        print("Simulation d'irradiance au sol sous tous les angles effectuée !")
    else : print("Simulation d'irradiance au sol sautée.")

    # Data Transformation
    if run_data_transformation():
        print("Transformation des données effectuée !\nDocuments disponibles : tableau effacement, angle et irradiance en fonction des heures de l'année.")
    else :
        print("Transformation des données non effectuée.")

    # STICS analysis
    if run_stics_simu() :
        print("Simulation STICS effectuée !")
    print("Fin du main")
