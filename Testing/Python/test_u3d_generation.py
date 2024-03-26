import os
import sys
import sysconfig

if sys.platform == 'win32':
    site_packages_dir = sysconfig.get_path('purelib')
    vtk_library_dir = f'{site_packages_dir}/vtk.libs'
    print(f'Adding DLL search path: {vtk_library_dir}')
    os.add_dll_directory(vtk_library_dir)

import vtk
from vtk.util.keys import StringKey
from vtk.vtkCommonCore import vtkInformationIterator
from vtk import vtkU3DExporter


def write_u3d(file_path, actors):
    render_window = vtk.vtkRenderWindow()
    render_window.OffScreenRenderingOn()
    renderer = vtk.vtkRenderer()
    render_window.AddRenderer(renderer)

    for actor in actors:
        renderer.AddActor(actor)

    renderer.ResetCamera()

    u3d_exporter = vtkU3DExporter.vtkU3DExporter()
    u3d_exporter.SetFileName(file_path)
    u3d_exporter.SetInput(render_window)
    u3d_exporter.Write()


def set_name_for_actor(name, actor):
    """
    Sets the name in the PropertyKeys of a vtkActor
    """
    key = StringKey.MakeKey("MeshName", "root")
    i = vtk.vtkInformation()
    i.Set(key, name)
    actor.SetPropertyKeys(i)


def get_name_for_actor(actor, keyName="MeshName"):
    """
    Returns the name from the PropertyKeys of a vtkActor
    """
    information = actor.GetPropertyKeys()
    if information is None:
        return None

    iterator = vtkInformationIterator()
    iterator.SetInformation(information)
    iterator.InitTraversal()
    while not iterator.IsDoneWithTraversal():
        key = iterator.GetCurrentKey()
        if key.GetName() == keyName:
            return information.Get(key)
        iterator.GoToNextItem()
    return None


def test_u3d_generation(tmp_path):

    # Create cube
    cube = vtk.vtkCubeSource()

    # Mapper
    cubeMapper = vtk.vtkPolyDataMapper()
    cubeMapper.SetInputConnection(cube.GetOutputPort())

    # Actor
    cubeActor = vtk.vtkActor()
    cubeActor.SetMapper(cubeMapper)
    assert get_name_for_actor(cubeActor) is None

    # Construct file paths
    filename = "test_report"
    file_path = tmp_path / filename
    u3d_path = file_path.with_suffix(".u3d")
    log_file_path = file_path.with_suffix(".u3d.DebugInfo.txt")

    # Write the u3d file to the file path
    write_u3d(file_path, [cubeActor])

    # Check that we have successfully created a U3D file
    assert u3d_path.exists(), "Failed to create the U3D file"

    # Check that the mesh is in the logs
    log_content = log_file_path.open().read()
    mesh_name = "Mesh2"
    assert f" {mesh_name}\n" in log_content, "{mesh_name} not found in U3D debug logs"
    