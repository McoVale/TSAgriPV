# coding: utf-8
import pandas as pd
import numpy as np

class Scenario:
    def __init__(self, file_path = ""):
        """
        Initialise l'objet Scenario avec un tableau de 24 colonnes (heures) et 12 lignes (mois),
        par défaut rempli de False. Le tableau peut être initialisé à partir d'un fichier Excel.
        """
        
        self.scenario = np.full((12,24), True, dtype=bool)
        if file_path is not "" :

            df = pd.read_excel(file_path, header=0, usecols=range(1, 25))
            for i in range(df.shape[0]):  # Pour chaque ligne
                for j in range(df.shape[1]):  # Pour chaque colonne
                    if df.iloc[i, j] == 0:
                        self.scenario[i, j] = False


    def count_erased_hours(self):
        """
        Renvoie le nombre d'heures effacées, c'est-à-dire le nombre de True dans le tableau.
        """
        return np.sum(self.scenario)
    
    def __str__(self):
        """
        Retourne une représentation textuelle du scénario.
        """
        return str(self.scenario)

# Exemple d'utilisation
if __name__ == "__main__":
    # Initialiser avec le tableau par défaut (tout False)
    scenario_default = Scenario()
    print("Scénario par défaut :")
    print(scenario_default)
    print("Nombre d'heures effacées :", scenario_default.count_erased_hours())

    # Initialiser à partir d'un tableau personnalisé
    custom_scenario = np.random.choice([True, False], size=(12, 24))
    scenario_custom = Scenario(custom_scenario)
    print("\nScénario personnalisé :")
    print(scenario_custom)
    print("Nombre d'heures effacées :", scenario_custom.count_erased_hours())

    # Initialiser à partir d'un fichier Excel
    # scenario_from_excel = Scenario()
    # scenario_from_excel.from_excel('path_to_your_file.xlsx')
    # print("\nScénario à partir d'un fichier Excel :")
    # print(scenario_from_excel)
    # print("Nombre d'heures effacées :", scenario_from_excel.count_erased_hours())