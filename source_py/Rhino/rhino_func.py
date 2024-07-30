from __future__ import division
import rhinoinside
rhinoinside.load()

import clr
clr.AddReference("Grasshopper")
from Grasshopper import DataTree
from Grasshopper.Kernel.Data import GH_Path as Path

import System
import Rhino.Display
import Rhino.Geometry as rg
from Grasshopper import DataTree
import Grasshopper.Kernel.Types as gh
import array

def objectify_output(object_name, output_data):
    """Wrap data into a single custom Python object that can later be de-serialized.

    This is meant to address the same issue as the wrap_output method but it does
    so by simply hiding the individual items from the Grasshopper UI within a custom
    parent object that other components can accept as input and de-objectify to
    get access to the data. This strategy is also useful for the case of standard
    object types like integers where the large number of data points slows down
    the Grasshopper UI when they are output.

    Args:
        object_name: Text for the name of the custom object that will wrap the data.
            This is how the object will display in the Grasshopper UI.
        output_data: A list of data to be stored under the data property of
            the output object.
    """
    class Objectifier(object):
        """Generic class for objectifying data."""

        def __init__(self, name, data):
            self.name = name
            self.data = data

        def ToString(self):
            return '{} ({} items)'.format(self.name, len(self.data))

    return Objectifier(object_name, output_data)

def de_objectify_output(objectified_data):
    """Extract the data from an object that was output from the objectify_output method.

    Args:
        objectified_data: An object that has been output from the objectify_output
            method for which data will be returned.
    """
    return objectified_data.data

def text_objects(text, plane, height, font='Arial',
                 horizontal_alignment=0, vertical_alignment=5):
    """Generate a Bake-able Grasshopper text object from a text string and ladybug Plane.

    Args:
        text: A text string to be converted to a a Grasshopper text object.
        plane: A Ladybug Plane object to locate and orient the text in the Rhino scene.
        height: A number for the height of the text in the Rhino scene.
        font: An optional text string for the font in which to draw the text.
        horizontal_alignment: An optional integer to specify the horizontal alignment
             of the text. Choose from: (0 = Left, 1 = Center, 2 = Right)
        vertical_alignment: An optional integer to specify the vertical alignment
             of the text. Choose from: (0 = Top, 1 = MiddleOfTop, 2 = BottomOfTop,
             3 = Middle, 4 = MiddleOfBottom, 5 = Bottom, 6 = BottomOfBoundingBox)
    """
    txt = Rhino.Display.Text3d(text, from_plane(plane), height)
    txt.FontFace = font
    txt.HorizontalAlignment = AlignmentTypes.horizontal(horizontal_alignment)
    txt.VerticalAlignment = AlignmentTypes.vertical(vertical_alignment)
    return TextGoo(txt)

def longest_list(values, index):
    """Get a value from a list while applying Grasshopper's longest-list logic.

    Args:
        values: An array of values from which a value will be pulled following
            longest list logic.
        index: Integer for the index of the item in the list to return. If this
            index is greater than the length of the values, the last item of the
            list will be returned.
    """
    try:
        return values[index]
    except IndexError:
        return values[-1]

def to_gridded_mesh3d_perso(brep, grid_size, offset_distance=0):
    """Create a gridded Ladybug Mesh3D from a Rhino Brep.

    This is useful since Rhino's grid meshing is often more beautiful than what
    ladybug_geometry can produce. However, the ladybug_geometry Face3D.get_mesh_grid
    method provides a workable alternative to this if it is needed.

    Args:
        brep: A Rhino Brep that will be converted into a gridded Ladybug Mesh3D.
        grid_size: A number for the grid size dimension with which to make the mesh.
        offset_distance: A number for the distance at which to offset the mesh from
            the underlying brep. The default is 0.
    """
    if not isinstance(brep, rg.Brep):  # it's likely an extrusion object
        brep = brep.ToBrep()  # extrusion objects must be cast to Brep in Rhino 8
    meshing_param = rg.MeshingParameters.Default
    meshing_param.MaximumEdgeLength = grid_size
    meshing_param.MinimumEdgeLength = grid_size
    meshing_param.GridAspectRatio = 1
    mesh_grids = rg.Mesh.CreateFromBrep(brep, meshing_param)
    if len(mesh_grids) == 1:  # only one mesh was generated
        mesh_grid = mesh_grids[0]
    else:  # join the meshes into one
        mesh_grid = rg.Mesh()
        for m_grid in mesh_grids:
            mesh_grid.Append(m_grid)
    if offset_distance != 0:
        temp_mesh = rg.Mesh()
        mesh_grid.Normals.UnitizeNormals()
        for pt, vec in zip(mesh_grid.Vertices, mesh_grid.Normals):
            # Startmodif
            vec3d = rg.Vector3d(vec) * offset_distance
            pt3d = rg.Point3d(pt)
            temp_mesh.Vertices.Add(pt3d + vec3d)
            # Endmodif
        for face in mesh_grid.Faces:
            temp_mesh.Faces.AddFace(face)
        mesh_grid = temp_mesh
    return to_mesh3d(mesh_grid)

def recipe_result(result):
    """Process a recipe result and handle the case that it's a list of list.

    Args:
        result: A recipe result to be processed.
    """
    if isinstance(result, (list, tuple)):
        return list_to_data_tree(result, s_type = str)
    return result

def list_to_data_tree(input, root_count=0, s_type = object):
    """Transform nested of lists or tuples to a Grasshopper DataTree.

    Args:
        input: A nested list of lists to be converted into a data tree.
        root_count: An integer for the starting path of the data tree.
        s_type: An optional data type (eg. float, int, str) that defines all of the
            data in the data tree. The default (object) works will all data types
            but the conversion to data trees can be more efficient if a more
            specific type is specified.
    """

    def proc(input, tree, track):
        for i, item in enumerate(input):
            if isinstance(item, (list, tuple, array.array)):  # ignore iterables like str
                track.append(i)
                proc(item, tree, track)
                track.pop()
            else:
                tree.Add(item, Path(*track))

    if input is not None:
        if not isinstance(s_type, type):
            raise TypeError("s_type must be a valid type")
        t = DataTree[s_type]()
        proc(input, t, [root_count])
        return t