# U3D requirements
find_library(U3D_IDTF_LIBRARY NAMES IDTF)
if(NOT U3D_IDTF_LIBRARY)
  message(FATAL_ERROR "Could not find U3D IDTF library")
endif()
message(STATUS "Found U3D IDTF library at: ${U3D_IDTF_LIBRARY}")

find_path(U3D_INCLUDE_DIR u3d/SceneConverterLib.h)
if(NOT U3D_INCLUDE_DIR)
    message(FATAL_ERROR "Could not find U3D include directory")
endif()
message(STATUS "Found U3D include directory: ${U3D_INCLUDE_DIR}")

add_library(U3D::IDTF UNKNOWN IMPORTED)
set_target_properties(U3D::IDTF PROPERTIES
  INTERFACE_INCLUDE_DIRECTORIES "${U3D_INCLUDE_DIR}"
  )
set_property(TARGET U3D::IDTF APPEND PROPERTY
  IMPORTED_LOCATION "${U3D_IDTF_LIBRARY}"
  )

# VTK module
set(classes
  vtkU3DExporter
  )

vtk_module_add_module(VTK::U3DExporter
  CLASSES ${classes}
  )
vtk_module_link(VTK::U3DExporter
  PUBLIC
    U3D::IDTF
  )
if(WIN32)
  vtk_module_link(VTK::U3DExporter
    PRIVATE
      winmm # For timeGetTime/timeBeginPeriod/timeEndPeriod
    )
endif()

if(VTK_WHEEL_BUILD)
  message(STATUS "Adding install rules for U3D components:")
  set(components "Runtime")
  foreach(component IN LISTS components)
    message(STATUS "  ${component}")
    if(NOT EXISTS "${U3D_BINARY_DIR}")
      message(FATAL_ERROR "Variable U3D_BINARY_DIR is set to an inexistent directory. U3D_BINARY_DIR [${U3D_BINARY_DIR}]")
      continue()
    endif()
    install(CODE "
unset(CMAKE_INSTALL_COMPONENT)
set(COMPONENT \"${component}\")
set(CMAKE_INSTALL_DO_STRIP 1)
include(\"${U3D_BINARY_DIR}/cmake_install.cmake\")
unset(CMAKE_INSTALL_COMPONENT)
")
  endforeach()
endif()
