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

_epw_file = "/../FRA_AC_Agen-La.Garenne.AP.075240_TMYx/FRA_AC_Agen-La.Garenne.AP.075240_TMYx.epw"

epw_data = epw.EPW(_epw_file)

location = epw_data.location
direct_normal_rad = epw_data.direct_normal_radiation
diffuse_horizontal_rad = epw_data.diffuse_horizontal_radiation

