from __future__ import division

import ladybug.epw as epw

import collections
import array
import math

import rhinoinside
rhinoinside.load()
import System
import Rhino

# try:
#     from Grasshopper.Kernel import GH_RuntimeMessageLevel as Message
# except ImportError as e:
#     raise ImportError("Failed to import Grasshopper.\n{}".format(e))

try:
    import Rhino.UI as rui
except ImportError as e:
    raise ImportError("Failed to import Rhino.\n{}".format(e))

# try:
#     import scriptcontext
# except ImportError:  # No Rhino doc is available.
#     print('Failed to import Rhino scriptcontext. Document counters will be unavailable.')

try:
    from System import Object
    from System.Windows import Forms
    from System import Environment
    import System.Security.Principal as sec
    import System.Threading.Tasks as tasks
except ImportError:
    print("Failed to import System.")

_epw_file = "/../FRA_AC_Agen-La.Garenne.AP.075240_TMYx/FRA_AC_Agen-La.Garenne.AP.075240_TMYx.epw"

epw_data = epw.EPW(_epw_file)
location = epw_data.location
dry_bulb_temperature = epw_data.dry_bulb_temperature
dew_point_temperature = epw_data.dew_point_temperature
relative_humidity = epw_data.relative_humidity
wind_speed = epw_data.wind_speed
wind_direction = epw_data.wind_direction
direct_normal_rad = epw_data.direct_normal_radiation
diffuse_horizontal_rad = epw_data.diffuse_horizontal_radiation
global_horizontal_rad = epw_data.global_horizontal_radiation
horizontal_infrared_rad = epw_data.horizontal_infrared_radiation_intensity
direct_normal_ill = epw_data.direct_normal_illuminance
diffuse_horizontal_ill = epw_data.diffuse_horizontal_illuminance
global_horizontal_ill = epw_data.global_horizontal_illuminance
total_sky_cover = epw_data.total_sky_cover
barometric_pressure = epw_data.atmospheric_station_pressure
model_year = epw_data.years
g_temp = epw_data.monthly_ground_temperature
ground_temperature = [g_temp[key] for key in sorted(g_temp.keys())]


# def all_required_inputs(component):
#     """Check that all required inputs on a component are present.

#     Note that this method needs required inputs to be written in the correct
#     format on the component in order to work (required inputs have a
#     single _ at the start and no _ at the end).

#     Args:
#         component: The grasshopper component object, which can be accessed through
#             the ghenv.Component call within Grasshopper API.

#     Returns:
#         True if all required inputs are present. False if they are not.
#     """
#     turn_off_old_tag(component)
#     is_input_missing = False
#     for param in component.Params.Input:
#         if param.NickName.startswith('_') and not param.NickName.endswith('_'):
#             missing = False
#             if not param.VolatileDataCount:
#                 missing = True
#             elif param.VolatileData[0][0] is None:
#                 missing = True

#             if missing is True:
#                 msg = 'Input parameter {} failed to collect data!'.format(param.NickName)
#                 print(msg)
#                 give_warning(component, msg)
#                 is_input_missing = True
#     return not is_input_missing