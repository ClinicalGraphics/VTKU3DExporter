from vtk import vtkU3DExporter


def test_basic_import():
    # Make sure it has some of the attributes we are expecting
    assert hasattr(vtkU3DExporter, 'vtkU3DExporter')
    assert hasattr(vtkU3DExporter.vtkU3DExporter, 'GetMeshCompression')
