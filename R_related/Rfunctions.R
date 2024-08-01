library(readxl)
library(SticsRFiles)
library(SticsOnR)
library(utils)

find_and_read_csv <- function(data_name, search_directory = ".") {
  # Construct the filename and file path
  file_name <- paste0("ratios_", data_name, ".csv")
  
  # Print the filename for reference
  print(paste("Filename:", file_name))
  
  # List all files in the search directory and subdirectories
  files <- list.files(search_directory, pattern = file_name, recursive = TRUE, full.names = TRUE)
  
  if (length(files) == 0) {
    stop(paste("File not found:", file_name))
  } else if (length(files) > 1) {
    warning(paste("Multiple files found with name:", file_name))
  }
  
  # Use the first file found (assuming unique or handle multiple if necessary)
  file_path <- files[1]
  
  # Display the relative and absolute paths
  relative_path <- file_path
  absolute_path <- normalizePath(file_path)
  
  print(paste("Relative file path:", relative_path))
  print(paste("Absolute file path:", absolute_path))
  
  # Read the CSV file
  data <- read.csv(file = file_path, header = TRUE)
  
  # Print the first few rows of the data for verification
  print(head(data))
  
  return(data)
}

#' Change the weather scenario based on irradiance ratios.
#'
#' This function reads irradiance ratios from a CSV file and applies these ratios 
#' to the weather data in the specified folder, creating new adjusted weather files.
#'
#' @param data_name A string representing the name of the data file (without extension).
#'                  The function will look for the file in the current directory with 
#'                  the format 'ratios_<data_name>.csv'.
#'
#' @return None. The function writes new weather files to the 'Rproject' directory.
change_scenar <- function(data_name) {
  # Construct the file path for the ratio data
  ratio_file_path <- paste0("DATA/ratios_", data_name, ".csv")
  
  normalized_path <- normalizePath(ratio_file_path)
  
  # Read the ratio data from the CSV file
  rapp <- read.csv(file = normalized_path, header = FALSE)
  
  # List all weather files in the 'weatherFilesSource' directory
  fichiers <- list.files("R_related/weatherFilesSource", full.names = TRUE)
  
  # Loop through each weather file
  for (i in 1:length(fichiers)) {
    current_met_file <- fichiers[i]
    
    # Import the current weather file
    data_scenar <- read.csv(file = current_met_file, sep = " ", header = FALSE)
    head(data_scenar)
    # Remove February 29th if it's a leap year
    if (nrow(data_scenar) == 366) {
      data_scenar <- data_scenar[-60, ]
    }
    
    # Apply the ratio to each day of the year
    for (j in 1:nrow(data_scenar)) {
      data_scenar[j, "V8"] <- round(data_scenar[j, "V8"] * rapp$V1[j], digits = 2)
    }
    head(data_scenar)
    # Create a new weather file with the same name but in the 'Rproject' directory
    new_file_path <- paste0("R_related/Rproject/", basename(current_met_file))
    write.table(data_scenar, file = new_file_path, sep = " ", row.names = FALSE, col.names = FALSE)
  }
  
  return(invisible(NULL))  # Return NULL invisibly
}

settings <- function(r_path_wd){
  #' This function has to set up the working environnement : create weatherFiles folder if not already present,
  #' link to javastics and to project folder,
  #'
  #'
  cat("Setting working directory to:", r_path_wd, "\n")
  setwd(dir = r_path_wd)
  cat("Get working dir : ", getwd(), "\n")
  
  javastics_path <- file.path("..", "JavaSTICS", "JavaStics.exe")
  javastics_path <- normalizePath(javastics_path, winslash = "/", mustWork = FALSE)
  cat("Javastics path : ", javastics_path, "\n")
  workspace_path <- file.path("Rproject")
  workspace_path <- normalizePath(workspace_path, winslash = "/", mustWork = FALSE)
  cat("Workspace path : ", workspace_path, "\n")
  
  weather_f_path <- "Rproject/weatherFiles/"
  
  if (!dir.exists(weather_f_path)) {
    dir.create(weather_f_path, recursive = TRUE)
    cat("Dossier créé:", weather_f_path, "\n")
  } else {
    cat("Le dossier existe déjà:", weather_f_path, "\n")
  }

  for (fichier in list.files("Rproject/weatherFiles/")) {
    file.copy(paste0("weatherFiles/", fichier), paste0(workspace_path, "/", fichier), overwrite = TRUE)
  }
}

change_STICS_setting <- function(xml_to_modify_path, param_name, val, values_id = NULL){
  #' This function is called from python when we need to change the value of a STICS parameter
  #' 
  if (is.null(values_id)) {
    SticsRFiles::set_param_xml(file = xml_to_modify_path,
                               param = param_name, 
                               values = val,
                               overwrite = TRUE,
                               )
  } else {
    SticsRFiles::set_param_xml(file = xml_to_modify_path,
                              param = param_name, 
                              values = unlist(val),
                              overwrite = TRUE,
                              value_id = unlist(values_id))
  }
}

# Function to copy weather files from source to working directory
copy_weather_files <- function(source_dir, workspace_path) {
  #' Copy weather files from source directory to working directory
  #'
  #' @param source_dir The directory containing the source weather files.
  #' @param workspace_path The working directory where files will be copied to.
  #'
  #' @return None
  
  # Copy each file from source directory to working directory
  for (fichier in list.files(source_dir)) {
    file.copy(paste0(source_dir, "/", fichier), paste0(workspace_path, "/", fichier), overwrite = TRUE)
  }
  return(NULL)
}

# Function to run a simulation
run_simulation <- function(javastics_path, workspace_path, usm) {
  #' Run a simulation using JavaStics
  #'
  #' @param javastics_path Path to the JavaStics executable.
  #' @param workspace_path Path to the workspace directory.
  #' @param usm Character vector of USM (Simulation Management Units) names.
  #'
  #' @return Data frame containing information about the simulation run.
  
  # Get information about the execution
  runs_inf <- run_javastics(javastics_path, workspace_path, usm = usm, verbose = TRUE)
  return(runs_inf)
}