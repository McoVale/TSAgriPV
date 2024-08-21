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
bdd_irr = pd.DataFrame()
bdd_irr['Month-Day-Hour'] = [ts.strftime('%m-%d-%H') for ts in timestamps]
JAVASTICS_PATH = 'JavaSTICS/'
R_STICS_WORKSPACE = 'R_related/Rproject/'

def import_general_settings():
    params_non_dict = pi.read_input_excel()
    parameters_dict = pi.transform_df_to_dict(params_non_dict)
    pi.modify_STICS_files(parameters_dict)
    return parameters_dict

def general_setup():
    pi.settings_dirs(PARAMS['PY_DATA_NAME'])
    PARAMS['PY_TYPE_PANEL'] = bool(PARAMS['PY_TYPE_PANEL'])
    PARAMS['PY_DO_RHINO_SIM'] = bool(PARAMS['PY_DO_RHINO_SIM'])
    PARAMS['PY_epw_name'] = "DATA/"+PARAMS['PY_epw_name']
    PARAMS['PY_wea'] = Wea.from_epw_file(PARAMS['PY_epw_name'], PARAMS['PY_timestep_wea'])
    PARAMS['PY_LARGEUR_AVIDE'] = (PARAMS['PY_RAMPANT']-4*PARAMS['PY_LARGEUR_BANDE'])/3
    PARAMS['PY_NB_PVP_RANGS'] = int(PARAMS['PY_GRID_SIZE'] / PARAMS['PY_ENTRAXE'])
    PARAMS['PY_LONGUEUR_PVP'] = PARAMS['PY_GRID_SIZE'] / (PARAMS['PY_NB_RANGS'])
    PARAMS['PY_LIST_ANGLES'] = np.arange(PARAMS['PY_start_angle'], PARAMS['PY_end_angle'] + 1, PARAMS['PY_PAS_ANGLE'])
    if PARAMS['PY_TYPE_CULT'] == 1 or PARAMS['PY_TYPE_CULT'] == 3:
        PARAMS['PY_HAUTEUR_MESURE'] = 1
    elif PARAMS['PY_TYPE_CULT'] == 2:
        PARAMS['PY_HAUTEUR_MESURE'] = 2.5
    PARAMS['PY_PATH_BDD_IRR'] = 'DATA/'+PARAMS['PY_DATA_NAME']+'/bdd_irr_'+PARAMS['PY_DATA_NAME']+'.xlsx'
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
    print("Récoltes indicatives :\n Zone témoin : ",res1[0]," t/ha ; Zone d'étude avec panneaux : ", res1[1], " t/ha."      )
    return True

if __name__ == "__main__":

    # Settings
    print("Import des paramètres ...")
    PARAMS = import_general_settings()
    general_setup()
    print("Paramétrage réalisé !")

    # Run Geom + Irradiance if wanted (PY_RHINO_SIM == TRUE)
    print("Partie simulation d'irradiance :")
    print(PARAMS['PY_PATH_BDD_IRR'])
    if PARAMS['PY_DO_RHINO_SIM'] == True :
        print("Simulation d'irradiance au sol en cours ...")
        rhino_geom.run_annual_irradiance_simulation(angles=PARAMS['PY_LIST_ANGLES'], wea=PARAMS['PY_wea'],tab_1=bdd_irr,hoys=HOYS,
                                                    output_path=PARAMS['PY_PATH_BDD_IRR'],FINESSE=PARAMS['PY_FINESSE'],GRID_SIZE=PARAMS['PY_GRID_SIZE'],
                                                    ENTRAXE=PARAMS['PY_ENTRAXE'],RAMPANT=PARAMS['PY_RAMPANT'],NB_PVP_RANGS=PARAMS['PY_NB_PVP_RANGS'],
                                                    ANGLE_ORIENTATION=PARAMS['PY_ANGLE_ORIENTATION'],TYPE_PANEL=PARAMS['PY_TYPE_PANEL'],
                                                    LARGEUR_BANDE=PARAMS['PY_LARGEUR_BANDE'],LARGEUR_AVIDE=PARAMS['PY_LARGEUR_AVIDE'],
                                                    LONGUEUR_PVP=PARAMS['PY_LONGUEUR_PVP'],HAUTEUR=PARAMS['PY_HAUTEUR'], cult=PARAMS['PY_TYPE_CULT'])
        print("Simulation d'irradiance au sol sous tous les angles effectuée !")
    else : print("Simulation d'irradiance au sol sautée.")

    # Data Transformation
    print("Début de la transformation des données")
    if run_data_transformation():
        print("Transformation des données effectuée !\nDocuments disponibles : tableau effacement, angle et irradiance en fonction des heures de l'année, dans le dossier ",PARAMS['PY_DATA_NAME'])
    else :
        print("Transformation des données non effectuée.")

    # STICS analysis
    print("Début de la simulation agro ...")
    if PARAMS['PY_DO_STICS_SIM'] == True :
        if run_stics_simu() :
            print("Simulation STICS effectuée, résultats STICS disponibles dans le dossier results.\n Veuillez les enregistrer avant de lancer une nouvelle simulation pour ne pas les perdre.")
    else : print("Simulation agronomique sautée.")
    print("Fin de l'application, veuillez fermer cette fenêtre.")
