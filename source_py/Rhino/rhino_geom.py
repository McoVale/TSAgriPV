from __future__ import division

import array
import math
import os
import shutil
import numpy as np
import pandas as pd


import rhinoinside
rhinoinside.load()

import clr
clr.AddReference("Grasshopper")
from Grasshopper import DataTree
from Grasshopper.Kernel.Data import GH_Path as Path
import System
import Rhino.Geometry as rg
from Rhino.Geometry import Point3d, Vector3d, Transform
from honeybee.model import Model
from honeybee.face import Face
from ladybug_geometry.geometry3d.face import Face3D
from ladybug_geometry.geometry3d.mesh import Mesh3D
from ladybug_geometry.geometry3d.plane import Plane
from ladybug_rhino.togeometry import to_mesh3d, to_face3d, to_vector3d
from honeybee_radiance.sensorgrid import SensorGrid
from honeybee.typing import clean_and_id_string
#from lbt_recipes.recipe import Recipe
from lbt_recipes.settings import RecipeSettings

from .rhino_func import longest_list, to_gridded_mesh3d_perso
from .rhino_irr import annual_irradiance

from lbt_recipes.version import check_radiance_date
# check the installed Radiance date and get the path to the gemdaymtx executable
check_radiance_date()

def create_surface(x, y, width, length):
    """
    Create a simple NURBS Rhino Surface from one of its four corners and its dimensions (width, length).

    Args:
        x (float): X-coordinate of origin corner
        y (float): Y-coordinate of origin corner
        width (float): Width of the surface
        length (float): Length of the surface

    Returns:
        surface : Rhino.Geometry.NurbsSurface, the created surface
    """
    pt1 = rg.Point3d(x, y, 0)
    pt2 = rg.Point3d(x, y + width, 0)
    pt3 = rg.Point3d(x + length, y + width, 0)
    pt4 = rg.Point3d(x + length, y, 0)
    
    # Create a surface from the previous point list, and return it
    surface = rg.NurbsSurface.CreateFromCorners(pt1, pt2, pt3, pt4)

    return surface

def create_panel_grid(grid_size, nb_rangs, nb_pvp_rangs, width, length, height, column_spacing, row_spacing, angle_orientation, angle_variable, semi_transp=False, bande=None, void_space=None):
    """
    According to the parameters, creates a grid of surfaces, later converted into Breps, representing the solar panels.

    Args:
        grid_size (float): Total size of the panel grid for simulation (can and will differ from the actual solar panel field)
        nb_rangs (int): Number of PVP per row
        nb_pvp_rangs (int): Number of rows
        width (float): Width of a PVP
        length (float): Length of a PVP
        column_spacing (float): Distance between two PVP rows (forced value (= ENTRAXE))
        row_spacing (float): Distance between two PVPs inside a row (can be equals to 0, forced value (=grid_size/nb_rangs))
        angle_orientation (int): Difference between the field axis (PVP supports' axis) and the North-South axis
        angle_variable (int): Tilt of the PVPs
        semi_transp (bool): False = classic PV Panel, one surface
                            True = Semi-transparent PV panel, composed of 4 strips of PV cells and 3 strips of space in between the cells.
        bande (float): Width of the PV cells strip, in case of semi-transparent panel
        void_space (float): Width of the void between PV cells strip, in case of semi-transparent panel

    Returns:
        Rhino.Geometry.Brep: Brep containing all the PVPs
    """
    final_brep = rg.Brep()

    for i in range(nb_rangs):
        for j in range(nb_pvp_rangs):
            # (x; y) are the coordinates of the current panel created
            x = (j * column_spacing) - grid_size / 2
            y = (i * row_spacing) - grid_size / 2
            surface = []

            if semi_transp:
                for h in range(4):
                    strip_x = x + h * (bande + void_space)
                    surface.append(create_surface(strip_x, y, bande, length))
            else:    
                surface.append(create_surface(x, y, width, length))
                
            # Rotation around the Y axis for each Brep individually
            center_of_surface = Point3d(x + width / 2, y + length / 2, 0)
            rotation_x = Transform.Rotation(angle_variable * (System.Math.PI / 180), Vector3d.YAxis, center_of_surface)
            for surf in surface:
                surf.Transform(rotation_x)
                # Adding it to the final returned brep
                final_brep.Append(surf.ToBrep())       

    # Global rotation around the Z axis at the center of the grid (origin)
    rotation_z = Transform.Rotation(-angle_orientation * (System.Math.PI / 180), Vector3d.ZAxis, rg.Point3d.Origin)
    final_brep.Transform(rotation_z)

    # Global translation on the Z axis, equivalent to the panel rotation axis height
    translation_z = Transform.Translation(0, 0, height)
    final_brep.Transform(translation_z)

    # Inversion of the orientation of the normals for proper operation of the Incident Radiation function
    final_brep.Flip()

    return final_brep

def create_sensor_grid(land_orientation, x, y, culture=False, entraxe=None, rampant=None, nb_lignes=None, grid_size=None):
    """
    Creates the surface from which the Incident Radiation will measure the ground irradiance.

    Args:
        land_orientation (int): Difference between the field axis (PVP supports' axis) and the North-South axis.
        culture (bool): If True, the measure surface will correspond to a rectangle that will fit under an arboriculture solar panel (used in vine for now).
                        If False, it will correspond to a square, that we could use in field crops.
        x (float): X-coordinate of the area of measures.
        y (float): Y-coordinate of the area of measures.
        entraxe (float): Distance between 2 rows of panels supports. None if culture is not arboriculture.
        rampant (float): Width of a PVP panel. None if culture is not arboriculture.
        nb_lignes (int): Number of PVP panels rows (= int(GRID_SIZE / ENTRAXE), calculated in settings).
        grid_size (float): Size of the grid.
        
    Returns:
        sensor_brep_list: List containing the created surfaces as Breps, which are then rotated and translated in the case of arboriculture.
    """
    brep_gen = rg.Brep()
    sensor_brep_list = []
    _TAILLE_SENSOR = 5  # Sensor side length = 5 meters

    if culture:
        # Create the coordinates of the first point of a measure grid that fits under an arboriculture PVP
        # (irradiance is not interesting in between vine rows)
        if x is None:
            x_arbo = math.floor(nb_lignes / 2) * entraxe + rampant / 2 - 0.5 - grid_size / 2
            y_arbo = -2.5
        else:
            x_arbo, y_arbo = x, y

        # Create a surface at the calculated center of the grid UNDER a panel, length = 5 and width = 1 m
        s = create_surface(x_arbo, y_arbo, _TAILLE_SENSOR, 1)
        brep_gen.Append(s.ToBrep())
        
        # Rotate the measure area to align it with the panels, using the same method and geometry references (ZAxis and Origin)
        rotation_z = rg.Transform.Rotation(-land_orientation * (math.pi / 180), Vector3d.ZAxis, rg.Point3d.Origin)
        brep_gen.Transform(rotation_z)

    else:
        # Create a square with TAILLE_SENSOR as the size of a side, center of the square is the origin of the Rhino Environment
        surface_brep = create_surface(-_TAILLE_SENSOR / 2, -_TAILLE_SENSOR / 2, _TAILLE_SENSOR, _TAILLE_SENSOR)
        brep_gen.Append(surface_brep.ToBrep())
    
    brep_gen.Flip()
    sensor_brep_list.append(brep_gen)

    return sensor_brep_list

def combine_grid_model(_model, grids_, views_=[]):
    """
    Add Radiance Sensor Grids and/or Views to a Honeybee Model.

    This assignment is necessary for any Radiance study, though whether a grid or a
    view is required for a particular type of study depends upon the recipe used.

    Multiple copies of this component can be used in series and each will add the
    grids or views to any that already exist.

    Args:
        _model (Model): A Honeybee Model to which the input grids_ and views_ will be assigned.
        grids_ (list): A list of Honeybee-Radiance SensorGrids, which will be assigned to the input _model.
        views_ (list): A list of Honeybee-Radiance Views, which will be assigned to the input _model.

    Returns:
        Model: The input Honeybee Model with the grids_ and views_ assigned to it.
    """
    assert isinstance(_model, Model), \
        'Expected Honeybee Model. Got {}.'.format(type(_model))
    
    # Duplicate the model to avoid modifying the input model
    model = _model.duplicate()
    
    # Add grids if the list is not empty
    if len(grids_) != 0:
        model.properties.radiance.add_sensor_grids(grids_)
    
    # Add views if the list is not empty
    if len(views_) != 0:
        model.properties.radiance.add_views(views_)

    return model

def convert_to_model(faces_, rooms_=None, shades_=None, apertures_=None, doors_=None, _name_="Grille"):
    """
    Create a Honeybee Model, which can be sent for simulation.

    Args:
        faces_ (list): A list of Honeybee Faces to be added to the Model. Note that
            faces without a parent Room are not allowed for energy models.
        rooms_ (list, optional): A list of Honeybee Rooms to be added to the Model. Note that at
            least one Room is necessary to make a simulate-able energy model.
        shades_ (list, optional): A list of Honeybee Shades to be added to the Model.
        apertures_ (list, optional): A list of Honeybee Apertures to be added to the Model. Note
            that apertures without a parent Face are not allowed for energy models.
        doors_ (list, optional): A list of Honeybee Doors to be added to the Model. Note
            that doors without a parent Face are not allowed for energy models.
        _name_ (str, optional): Text to be used for the Model name and to be incorporated into a unique
            model identifier. If no name is provided, it will be "unnamed" and
            a unique model identifier will be auto-generated.

    Returns:
        Model: A Honeybee Model object possessing all of the input geometry
            objects.
    """
    try:  # Import the ladybug_rhino dependencies
        from ladybug_rhino.config import units_system, tolerance, angle_tolerance
        from honeybee.typing import clean_string, clean_and_id_string
    except ImportError as e:
        raise ImportError('\nFailed to import ladybug_rhino:\n\t{}'.format(e))
    
    # Set a default name and get the Rhino Model units
    name = clean_string(_name_) if _name_ is not None else clean_and_id_string('unnamed')
    units = units_system()

    # Create the model
    model = Model(name, rooms_, faces_, shades_, apertures_, doors_,
                  units=units, tolerance=tolerance, angle_tolerance=angle_tolerance)

    return model

def brep_to_face(_geo, _name_ = [], _type_ = None, _bc_ = None):
    """
    Create Honeybee Face.

    Args:
        _geo: Rhino Brep or Mesh geometry.
        _name_ (list, optional): Text to set the name for the Face and to be incorporated into
            unique Face identifier. If the name is not provided, a random name
            will be assigned.
        _type_ (str, optional): Text for the face type. The face type will be used to set the
            material and construction for the surface if they are not assigned
            through the inputs below. The default is automatically set based
            on the normal direction of the Face (up being RoofCeiling, down
            being Floor and vertically-oriented being Wall).
            Choose from the following:
                - Wall
                - RoofCeiling
                - Floor
                - AirBoundary
        _bc_ (str, optional): Text for the boundary condition of the face. The boundary condition
            is also used to assign default materials and constructions as well as
            the nature of heat exchange across the face in energy simulation.
            Default is Outdoors unless all vertices of the geometry lie below
            the XY plane, in which case it will be set to Ground.
            Choose from the following:
                - Outdoors
                - Ground
                - Adiabatic

    Returns:
        list: A list of Honeybee Faces. These can be used directly in radiance simulations
              or can be added to a Honeybee room for energy simulation.
    """
    faces = []  # list of faces that will be returned
    for j, geo in enumerate(_geo):
        # Set a default Face name if not provided
        if len(_name_) == 0:
            name = display_name = clean_and_id_string('Face')
        else:
            display_name = '{}_{}'.format(longest_list(_name_, j), j + 1) \
                if len(_name_) != len(_geo) else longest_list(_name_, j)
            name = clean_and_id_string(display_name)
        typ = _type_
        bc = _bc_
        
        # Convert geometry to Face3D
        lb_faces = to_face3d(geo)
        for i, lb_face in enumerate(lb_faces):
            face_name = '{}_{}'.format(name, i) if len(lb_faces) > 1 else name
            hb_face = Face(face_name, lb_face, typ, bc)
            hb_face.display_name = display_name

            faces.append(hb_face)  # Collect the final Faces
        
    return faces

def brep_to_pts_mesh(_geometry, _grid_size, _offset_dist_ = 1, quad_only_ = False):
    """
    Generate a mesh with corresponding test points from a Rhino Brep (or Mesh).

    Args:
        _geometry: Brep or Mesh from which to generate the points and grid.
        _grid_size: Number for the size of the test grid.
        _offset_dist_: Number for the distance to move points from the surfaces
            of the input _geometry. Typically, this should be a small positive
            number to ensure points are not blocked by the mesh. (Default: 0).
        quad_only_: Boolean to note whether meshing should be done using Rhino's
            defaults (False), which fills the entire _geometry to the edges
            with both quad and tringulated faces, or a mesh with only quad
            faces should be generated.
            FOR ADVANCED USERS: This input can also be a vector object that will
            be used to set the orientation of the quad-only grid. Note that,
            if a vector is input here that is not aligned with the plane of
            the input _geometry, an error will be raised.

    Returns:
        points: Test points at the center of each mesh face.
    """
    # check the input and generate the mesh.
    _offset_dist_ = _offset_dist_ or 0
    if quad_only_:  # use Ladybug's built-in meshing methods
        lb_faces = to_face3d(_geometry)
        try:
            x_axis = to_vector3d(quad_only_)
            lb_faces = [Face3D(f.boundary, Plane(f.normal, f[0], x_axis), f.holes)
                        for f in lb_faces]
        except AttributeError:
            pass  # no plane connected; just use default orientation
        lb_meshes = []
        for geo in lb_faces:
            try:
                lb_meshes.append(geo.mesh_grid(_grid_size, offset=_offset_dist_))
            except AssertionError:  # tiny geometry not compatible with quad faces
                continue
        if len(lb_meshes) == 0:
            lb_mesh = None
        elif len(lb_meshes) == 1:
            lb_mesh = lb_meshes[0]
        elif len(lb_meshes) > 1:
            lb_mesh = Mesh3D.join_meshes(lb_meshes)
    else:  # use Rhino's default meshing
        lb_mesh = to_gridded_mesh3d_perso(_geometry, _grid_size, _offset_dist_)
    
    # generate the test points, vectors, and areas.
    if lb_mesh is not None:
        points = [pt for pt in lb_mesh.face_centroids]

    return points

def convert_to_grid(_positions, _name_ = '', _directions_ = [], mesh_ = None, base_geo_ = None):
    """
    Create a Sensor Grid object that can be used in a grid-based recipe.

    Args:
        _name_: A name for this sensor grid.
        _positions: A list or a datatree of points with one point for the position
            of each sensor. Each branch of the datatree will be considered as a
            separate sensor grid.
        _directions_: A list or a datatree of vectors with one vector for the
            direction of each sensor. The input here MUST therefore align with
            the input _positions. If no value is provided (0, 0, 1) will be
            assigned for all the sensors.
        mesh_: An optional mesh that aligns with the sensors. This is useful for
            generating visualizations of the sensor grid beyond the sensor
            positions. Note that the number of sensors in the grid must match
            the number of faces or the number of vertices within the mesh.
        base_geo_: An optional Brep for the geometry used to make the grid. There are
            no restrictions on how this brep relates to the sensors and it is
            provided only to assist with the display of the grid when the number
            of sensors or the mesh is too large to be practically visualized.

    Returns:
        grid: A SensorGrid object that can be used in a grid-based recipe.
    """
    # Set the default name and process the points to tuples
    pts = []
    for pt in _positions:
        pts.append((pt.x, pt.y, pt.z))

    # Create the sensor grid object
    id = _name_
    if len(_directions_) == 0:
        grid = SensorGrid.from_planar_positions(id, pts, (0, 0, 1))
    else:
        vecs = [(vec.X, vec.Y, vec.Z) for vec in _directions_]
        grid = SensorGrid.from_position_and_direction(id, pts, vecs)
        
    if mesh_ is not None:
        grid.mesh = to_mesh3d(mesh_)
    if base_geo_ is not None:
        grid.base_geometry = to_face3d(base_geo_)

    return grid

def run_annual_irradiance_simulation(angles, wea, tab_1, hoys, output_path, FINESSE, GRID_SIZE, ENTRAXE, RAMPANT, NB_PVP_RANGS, ANGLE_ORIENTATION, TYPE_PANEL, LARGEUR_BANDE, LARGEUR_AVIDE, LONGUEUR_PVP, HAUTEUR):
    """
    Run annual irradiance simulations for a range of panel tilt angles and export the results to an Excel file.
    
    Args:
        angles: List of tilt angles to simulate.
        wea: A Wea object or path to a .wea or .epw file.
        tab_1: DataFrame to store the results.
        hoys: List of hours of the year to be considered in the results.
        output_path: Path to the output Excel file where results will be saved.
        FINESSE: Grid size for mesh resolution.
        GRID_SIZE: Grid size for panel creation.
        ENTRAXE: Distance between rows of panels.
        RAMPANT: Inclination of the panels.
        NB_PVP_RANGS: Number of panels per row.
        ANGLE_ORIENTATION: Orientation angle of the panels.
        TYPE_PANEL: Type of panels to be used.
        LARGEUR_BANDE: Width of the panel band.
        LARGEUR_AVIDE: Width of the panel slot.
        LONGUEUR_PVP: Length of the panels.
        HAUTEUR: Height of the panels.
    
    Returns:
        None
    """
    # Paths and settings
    path_resultsHB_AI = os.path.join('Annual_Irr_Results')
    print(path_resultsHB_AI)
    settings_HB_AI = RecipeSettings(path_resultsHB_AI)
    settings_HB_AI_CT = RecipeSettings(path_resultsHB_AI+'_CT')

    ### Run simulation with CONTROL area -------------------------------------------
    # Create classic geometry
    panels_CT = rg.Brep()
    panels_CT.Append(create_surface(40, 40, 0.1, 0.1).ToBrep())
    ground_CT = create_sensor_grid(ANGLE_ORIENTATION, 40, 40, culture=True)

    # Convert to Model for control area
    panels_CT_faces = brep_to_face([panels_CT])
    panel_CT_model = convert_to_model(panels_CT_faces)
    ground_CT_grid = brep_to_pts_mesh(ground_CT[0], _grid_size=FINESSE)  # BREP TO POINTS
    ground_CT_grid_sensor = convert_to_grid(ground_CT_grid, 'ID_CT')
    panel_CT_model_gridded = combine_grid_model(panel_CT_model, [ground_CT_grid_sensor])  # MODEL COMBINED WITH GRID

    # Run annual irradiance function
    annual_irradiance(_model=panel_CT_model_gridded, _wea=wea, run_settings_=settings_HB_AI_CT) 

    ### Run simulation with STUDY area -------------------------------------------
    # Create measurement grid
    ground = create_sensor_grid(ANGLE_ORIENTATION, None, None, culture=True, 
                                    entraxe=ENTRAXE, rampant=RAMPANT, nb_lignes=NB_PVP_RANGS, grid_size=GRID_SIZE)
    ground_grid = brep_to_pts_mesh(ground[0], _grid_size=FINESSE)  # BREP TO POINTS
    ground_grid_sensor = convert_to_grid(ground_grid, 'ID_1')

    # Loop over angles and run simulations
    for index, angle in enumerate(angles):
        # Create panel geometry
        print("Boucle simulation, angle numéro :",index+1)
        final_rotated_brep = create_panel_grid(GRID_SIZE, NB_PVP_RANGS, NB_PVP_RANGS, RAMPANT, LONGUEUR_PVP, HAUTEUR, ENTRAXE, LONGUEUR_PVP, ANGLE_ORIENTATION, angle,
                                               TYPE_PANEL, LARGEUR_BANDE, LARGEUR_AVIDE)

        # Convert to Model
        panel_faces = brep_to_face([final_rotated_brep])
        panel_model = convert_to_model(panel_faces)
        panel_model_gridded = combine_grid_model(panel_model, [ground_grid_sensor])  # MODEL COMBINED WITH GRID

        # Run annual irradiance
        annual_irradiance(_model=panel_model_gridded, _wea=wea, run_settings_=settings_HB_AI)

        # Export data to container
        sun_up_hours = pd.read_csv('Annual_Irr_Results/annual_irradiance/results/total/sun-up-hours.txt', header=None).squeeze()
        sun_up_hours = sun_up_hours - 0.5

        ill_data = pd.read_csv('Annual_Irr_Results/annual_irradiance/results/total/ID_1.ill', delim_whitespace=True, header=None)
        ill_data_mean = ill_data.mean()

        angle_txt = str(angle)
        tab_1[angle_txt] = 0
        for hour in hoys:
            if hour in sun_up_hours.values:
                index = sun_up_hours[sun_up_hours == hour].index[0]
                tab_1.at[hour, angle_txt] = ill_data_mean[index]

        # Clean up
        if os.path.exists(path_resultsHB_AI):
            shutil.rmtree(path_resultsHB_AI)
            print(f"Le dossier '{path_resultsHB_AI}' a été supprimé avec succès.")
        else:
            print(f"Le dossier '{path_resultsHB_AI}' n'existe pas.")

    # Add control light simulation results to table
    sun_up_hours = pd.read_csv('Annual_Irr_Results_CT/annual_irradiance/results/total/sun-up-hours.txt', header=None).squeeze()
    sun_up_hours = sun_up_hours - 0.5

    ill_data = pd.read_csv('Annual_Irr_Results_CT/annual_irradiance/results/total/ID_CT.ill', delim_whitespace=True, header=None)
    ill_data_mean = ill_data.mean()

    CT_txt = 'temoin'
    tab_1[CT_txt] = 0
    for hour in hoys:
        if hour in sun_up_hours.values:
            index = sun_up_hours[sun_up_hours == hour].index[0]
            tab_1.at[hour, CT_txt] = ill_data_mean[index]

    # Clean up control area folder
    if os.path.exists(path_resultsHB_AI + '_CT'):
        shutil.rmtree(path_resultsHB_AI + '_CT')
        print(f"Le dossier '{path_resultsHB_AI + '_CT'}' a été supprimé avec succès.")
    else:
        print(f"Le dossier '{path_resultsHB_AI + '_CT'}' n'existe pas.")

    # Export results to Excel
    print(output_path)
    tab_1.to_excel(output_path, index=False, header=True)
##