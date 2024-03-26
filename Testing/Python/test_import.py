import os
import sys
import sysconfig

if sys.platform == 'win32':
    site_packages_dir = sysconfig.get_path('purelib')
    vtk_library_dir = f'{site_packages_dir}/vtk.libs'
    print(f'Adding DLL search path: {vtk_library_dir}')
    os.add_dll_directory(vtk_library_dir)

from vtk import vtkU3DExporter


def test_basic_import():
    # Make sure it has some of the attributes we are expecting
    assert hasattr(vtkU3DExporter, 'vtkU3DExporter')
    assert hasattr(vtkU3DExporter.vtkU3DExporter, 'GetMeshCompression')
