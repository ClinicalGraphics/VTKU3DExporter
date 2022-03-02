vtk_add_test_cxx(vtkU3DExporterCxxTests tests
  vtkU3DExporterTest.cxx,NO_VALID,NO_OUTPUT
  )

vtk_test_cxx_executable(vtkU3DExporterCxxTests tests
  RENDERING_FACTORY
  )