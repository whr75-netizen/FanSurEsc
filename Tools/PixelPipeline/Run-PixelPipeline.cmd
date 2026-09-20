@echo off
setlocal
pushd "%~dp0\..\.."
set "PIXEL_PYTHON=C:\Users\JG\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
set "PIXEL_RUN=LocalOnly\PixelPipeline21\run01"
if not "%~1"=="" set "PIXEL_RUN=%~1"
"%PIXEL_PYTHON%" -B Tools\PixelPipeline\graph_driver.py run --run-dir "%PIXEL_RUN%" --contract Tools\PixelPipeline\desk_contract.json --code-file Tools\PixelPipeline\common.py --code-file Tools\PixelPipeline\material.py --code-file Tools\PixelPipeline\blender_stage.py --code-file Tools\PixelDesk\vendor\perfectpixel-archive\perfect_pixel_noCV2.py
set "PIXEL_EXIT=%ERRORLEVEL%"
popd
exit /b %PIXEL_EXIT%
