#Petit test des fonction STICSRFiles
setwd(dir = "C:/Users/maceo.valente/Documents/Automatisation/TEST_MVA/TSAgriPV/R_related")
library(readxl)
library(SticsRFiles)
library(SticsOnR)
javastics_path = file.path("..","JavaSTICS")
workspace_path = file.path("Rproject")

typeof(SticsRFiles::get_param_xml(file = file.path(workspace_path,"sols.xml"), param = c("epc"), select = "sol",
                           select_value = c("VignePioGre")))

SticsRFiles::set_param_xml(file = file.path(workspace_path,"sols.xml"), param = c("HCCF"), select = "sol",
                           select_value = c("VignePioGre"), values = c(31,32,33,34,35), value_id = c(1,2,3,4,5), overwrite = TRUE)


a = list(31,32,33)
typeof(a)
values = list(c(20:24, 10:14), c(50:54, 40:44))

values[1]



SticsRFiles::set_param_xml(file = file.path(workspace_path,"VignePioGre_ini.xml"), param = c("densinitial"), select = "ini",select_value = c("VignePioGre"), values = c(0.0044,0.5,0.5,0,0), value_id = c(1,2,3,4,5), overwrite = TRUE)

sct = "ini"
sel_val = "VignePioGre_ini"
SticsRFiles::set_param_xml(file = file.path(workspace_path,"VignePioGre_ini.xml"), param = c("densinitial"),values = c(0.5,0.5,0.0022,10,0), value_id = c(0,1,2,3,4),overwrite = TRUE)


SticsRFiles::set_param_xml(file = file.path(workspace_path,"usms.xml"), param = c("datefin"),values = c(214),overwrite = TRUE)

