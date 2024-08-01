library(SticsOnR)
library(SticsRFiles)
setwd(dir = "C:/Users/maceo.valente/Documents/Automatisation/TEST_MVA/TSAgriPV/R_related")
getwd()
source("Rfunctions.R")

##############################################################
###Using usms from R, changing the weather file###
##############################################################

javastics_path = file.path("..","JavaSTICS")
workspace_path = file.path("Rproject")


#########
##STEPS##
#########

#0 : Setup 
#Copying source weatherFile from weatherFileSource to working directory
for (fichier in list.files("weatherFilesSource/")) {
  file.copy(paste0("weatherFilesSource/", fichier), paste0(workspace_path, "/", fichier), overwrite = TRUE)
}


change_scenar("piolenc")

#Run simulation
runs_inf <- run_javastics(javastics_path, workspace_path,
                          usm = c("VignePioGre"), verbose = TRUE)

#Get the results
resultsSimu2 <- read.csv("Rproject/mod_sVignePioGre.sti", header = TRUE, sep = ";")
yieldMaFruit2 <- round(max(resultsSimu2["mafruit"])*1/.2608, digits = 2)
yieldPdsFruitFrais2 <- max(resultsSimu2["pdsfruitfrais"])

print(yieldMaFruit2)
print(yieldPdsFruitFrais2)


