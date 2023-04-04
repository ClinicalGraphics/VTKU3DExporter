# vtk-u3dexporter

U3D is a format for 3D models that can be embedded into PDF.

## License

This project is distributed under the Apache license. Please see the [LICENSE][LICENSE] file for details.

[LICENSE]: https://github.com/ClinicalGraphics/VTKU3DExporter/blob/main/LICENSE

## Running the build locally on Windows

First time:

```pwsh
py -m venv .venv
.venv/Scripts/python -m pip install -U pip
.venv/Scripts/pip install cibuildwheel
$env:CIBW_TEST_COMMAND = "pip install -r {package}/Testing/Python/requirements.txt && pytest -v {package}/Testing/Python"
.venv/Scripts/cibuildwheel --only cp39-win_amd64
```

Subsequent builds require clearing the `_skbuild` and `wheelhouse` folders or they will fail:

```pwsh
Remove-Item -Recurse -Force ./_skbuild && Remove-Item -Recurse -Force ./wheelhouse && .venv/Scripts/cibuildwheel --only cp39-win_amd64
```

## Testing the build locally on Windows

First run the build locally as described above.

```pwsh
.venv/Scripts/pip install -r Testing/Python/requirements.txt
.venv/Scripts/pip install --force-reinstall wheelhouse/vtk_u3dexporter-xxxxxx-cp39-cp39-win_amd64.whl
.venv/Scripts/pytest -v Testing/Python
```

## Testing pyinstaller support locally on Windows

First ensure tests pass locally as described above.

```pwsh
Copy-Item .\lib\vtkmodules\__pyinstaller_vtkU3DExporter\hook-vtk.py .\.venv\Lib\site-packages\vtkmodules\__pyinstaller_vtkU3DExporter\hook-vtk.py
.venv/Scripts/pyinstaller --noconfirm --clean --distpath ./pyi/dist --workpath ./pyi/build --specpath Testing/Python Testing/Python/pyi_test_program.py
.\pyi\dist\pyi_test_program\pyi_test_program.exe
```
