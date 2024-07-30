from source_py import param_inputs as pi

PARAMS = {}

def import_all_settings():
    df = pi.read_input_excel()
    PARAMS = pi.transform_df_to_dict(df)
    pi.modify_STICS_files(PARAMS)



if __name__ == "__main__":

    import_all_settings()

    # valeur = mon_dictionnaire[cle]

    print("Fin du main")
