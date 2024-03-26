import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys

from skbuild import setup


VTK_DEFAULT_WHEEL_SDK_VERSION = "9.3.0"


vtk_module_source_dir = Path(__file__).parent.resolve()


def vtk_wheel_sdk_version():
    return os.getenv("VTK_WHEEL_SDK_VERSION", VTK_DEFAULT_WHEEL_SDK_VERSION)


def vtk_wheel_sdk_name(sdk_version=None):
    """Return the VTK wheel SDK name.
    """

    if sdk_version is None:
        sdk_version = vtk_wheel_sdk_version()

    py_version_short = "".join(map(str, sys.version_info[:2]))

    py_version = f"cp{py_version_short}-cp{py_version_short}"
    if sys.version_info[:2] < (3, 8):
        # Need to add "m" at the end
        py_version += "m"

    platform_suffixes = {
        "linux": "manylinux_2_17_x86_64.manylinux2014_x86_64",
        "darwin": "macosx_10_10_x86_64",
        "win32": "win_amd64",
    }

    if sys.platform not in platform_suffixes:
        raise NotImplementedError(sys.platform)

    platform_suffix = platform_suffixes[sys.platform]

    if sys.platform == "darwin":
        is_arm = (
            platform.machine() == "arm64" or
            # ARCHFLAGS: see https://github.com/pypa/cibuildwheel/discussions/997
            os.getenv("ARCHFLAGS") == "-arch arm64"
        )
        if is_arm:
            # It's an arm64 build
            platform_suffix = "macosx_11_0_arm64"

    prefix = "vtk-wheel-sdk"
    wheel_sdk_name = f"{prefix}-{sdk_version}-{py_version}-{platform_suffix}"

    return wheel_sdk_name


def auto_download_vtk_wheel_sdk():
    # Automatically download the VTK wheel SDK based upon the current platform
    # and python version.
    # If the download location changes, we may need to change the logic here.
    # Returns the path to the unpacked SDK.

    base_url = "https://vtk.org/files/wheel-sdks/"
    prefix = "vtk-wheel-sdk"

    wheel_sdk_name = vtk_wheel_sdk_name()

    default_install_path = Path(".").resolve() / f"_deps/{wheel_sdk_name}"
    install_path = Path(os.getenv("VTK_WHEEL_SDK_INSTALL_PATH",
                                  default_install_path))

    if install_path.exists():
        # It already exists, just return it
        return install_path.as_posix()

    # Need to download it
    full_name = f"{wheel_sdk_name}.tar.xz"
    url = f"{base_url}{full_name}"

    script_path = str(vtk_module_source_dir /
                      "FetchFromUrl.cmake")

    cmd = [
        "cmake",
        f"-DFETCH_FROM_URL_PROJECT_NAME={prefix}",
        f"-DFETCH_FROM_URL_INSTALL_LOCATION={install_path.as_posix()}",
        f"-DFETCH_FROM_URL_URL={url}",
        "-P", script_path,
    ]
    subprocess.check_call(cmd)

    return install_path.as_posix()


def auto_download_vtk_external_module():
    # Automatically download the VTKExternalModule repository.
    # Returns the path to the VTKExternalModule directory.

    external_module_path = Path(".").resolve() / "_deps/VTKExternalModule"
    if external_module_path.exists():
        # It must have already been downloaded. Just return it.
        return external_module_path.as_posix()

    # Run the script to download it
    script_path = str(vtk_module_source_dir /
                      "FetchVTKExternalModule.cmake")
    cmd = [
        "cmake",
        "-DFETCH_VTKExternalModule_INSTALL_LOCATION=" +
        external_module_path.as_posix(),
        "-P", script_path,
    ]
    subprocess.check_call(cmd)
    return external_module_path.as_posix()


def auto_build_vtk_compile_tools():
    """Automatically download the VTK sources and build the compile tools.

    Returns the path to the VTKCompileTools build direcory.
    """

    sdk_version = vtk_wheel_sdk_version()

    wheel_sdk_name = vtk_wheel_sdk_name(sdk_version=sdk_version)

    populate_path = Path("..").resolve() / f"{wheel_sdk_name}-deps/VTKCompileTools"
    compile_tools_path = Path("..").resolve() / f"{wheel_sdk_name}-deps/VTKCompileTools-build"

    script_path = str(vtk_module_source_dir / "BuildVTKCompileTools.cmake")

    cmd = [
        "cmake",
        f"-DVTKCompileTools_POPULATE_DIR:PATH={populate_path}",
        f"-DVTK_WHEEL_SDK_VERSION:STRING={sdk_version}",
        f"-DVTKCompileTools_DIR:PATH={compile_tools_path}",
        "-P", script_path,
    ]
    subprocess.check_call(cmd)
    return compile_tools_path.as_posix()


vtk_wheel_sdk_path = os.getenv("VTK_WHEEL_SDK_PATH")
if vtk_wheel_sdk_path is None:
    vtk_wheel_sdk_path = auto_download_vtk_wheel_sdk()

# Find the cmake dir
cmake_glob = list(Path(vtk_wheel_sdk_path).glob("**/headers/cmake"))
if len(cmake_glob) != 1:
    raise Exception(f"Unable to find cmake directory in vtk_wheel_sdk_path [{vtk_wheel_sdk_path}]")

vtk_wheel_sdk_cmake_path = cmake_glob[0]

vtk_external_module_path = os.getenv("VTK_EXTERNAL_MODULE_PATH")
if vtk_external_module_path is None:
    # If it was not provided, clone it into a temporary directory
    # Since we are using pyproject.toml, it will get removed automatically
    vtk_external_module_path = auto_download_vtk_external_module()

python3_executable = os.getenv("Python3_EXECUTABLE")
if python3_executable is None:
    python3_executable = shutil.which("python")

if python3_executable is None:
    msg = "Unable find python executable, please set Python3_EXECUTABLE"
    raise Exception(msg)

cmake_args = [
    "-DVTK_MODULE_NAME:STRING=U3DExporter",
    f"-DVTK_MODULE_SOURCE_DIR:PATH={vtk_module_source_dir}",
    f"-DVTK_MODULE_CMAKE_MODULE_PATH:PATH={vtk_wheel_sdk_cmake_path}",
    "-DVTK_MODULE_SUPERBUILD:BOOL=ON",
    "-DVTK_MODULE_EXTERNAL_PROJECT_DEPENDENCIES:STRING=U3D",
    "-DVTK_MODULE_EXTERNAL_PROJECT_CMAKE_CACHE_ARGS:STRING=VTK_USE_X;VTK_USE_COCOA",
    f"-DVTK_DIR:PATH={vtk_wheel_sdk_cmake_path}",
    "-DCMAKE_INSTALL_LIBDIR:STRING=lib",
    f"-DPython3_EXECUTABLE:FILEPATH={python3_executable}",
    "-DVTK_WHEEL_BUILD:BOOL=ON",
    "-S", vtk_external_module_path,
]

if sys.platform == "linux":
    # We currently have to add this for the render window to get compiled
    cmake_args.append("-DVTK_USE_X:BOOL=ON")

    if os.getenv("LINUX_VTK_U3DEXPORTER_USE_COMPATIBLE_ABI") == "1":
        # If building locally, it is necessary to set this in order to
        # produce a wheel that can be used. Otherwise, the VTK symbols
        # will not match those in the actual VTK wheel.
        cmake_args.append("-DCMAKE_CXX_FLAGS=-D_GLIBCXX_USE_CXX11_ABI=0")

elif sys.platform == "darwin":
    # We currently have to add this for the render window to get compiled
    cmake_args.append("-DVTK_USE_COCOA:BOOL=ON")

    if os.getenv("ARCHFLAGS") == "-arch arm64":
        cmake_args.append("-DCMAKE_CROSSCOMPILING:BOOL=ON")

        # We are cross-compiling and need to set CMAKE_SYSTEM_NAME as well.
        cmake_args.append("-DCMAKE_SYSTEM_NAME=Darwin")

        vtk_compile_tools_dir = auto_build_vtk_compile_tools()
        cmake_args.append(f"-DVTKCompileTools_DIR:PATH={vtk_compile_tools_dir}")


long_description = (vtk_module_source_dir / "README.md").read_text(encoding="utf-8")

setup(
    name="vtk-u3dexporter",
    description="General-purpose features that may be integrated into VTK library in the future.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/ClinicalGraphics/VTKU3DExporter",
    author="Jean-Christophe Fillion-Robin",
    email="jcfr@kitware.com",
    license="Apache Software License",
    classifiers=[
        "Development Status :: 4 - Beta",
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python :: 3",
        "Topic :: Scientific/Engineering :: Medical Science Apps.",
    ],
    keywords="",
    packages=["vtkmodules", "vtkmodules.__pyinstaller_vtkU3DExporter"],
    package_dir={
        "vtkmodules": "lib/vtkmodules",
        "vtkmodules.__pyinstaller_vtkU3DExporter": "lib/vtkmodules/__pyinstaller_vtkU3DExporter",
    },
    cmake_args=cmake_args,
    install_requires=["vtk==9.3.0"],
    project_urls={  # Optional
        "Bug Reports": "https://github.com/ClinicalGraphics/VTKU3DExporter/issues",
        "Source": "https://github.com/ClinicalGraphics/VTKU3DExporter/",
    },
    entry_points={
        "pyinstaller40": [
            "hook-dirs = vtkmodules.__pyinstaller_vtkU3DExporter:get_hook_dirs",
        ],
    },
)
