#System
import os
import shutil
import numpy as np
import pandas as pd
import array
import math
import System
from __future__ import division

#Rhino
import rhinoinside
rhinoinside.load()

import clr
clr.AddReference("Grasshopper")
from Grasshopper import DataTree
from Grasshopper.Kernel.Data import GH_Path as Path
import Rhino.Geometry as rg
from Rhino.Geometry import Point3d, Plane, Brep, Vector3d
from Rhino.Geometry import Surface as RhinoSurface

from Rhino.Geometry import Transform
from Rhino.FileIO import File3dm
from Rhino import UnitSystem

#LadybugTools
import ladybug.epw as epw
from lbt_recipes.version import check_radiance_date
from ladybug_rhino.fromgeometry import from_point3d