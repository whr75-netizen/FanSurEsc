@echo off
setlocal
set "PIXEL_UNIFORM_PYTHON=C:\Users\JG\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
set "PIXEL_UNIFORM_SCRIPT=%~dp0web.py"
set "PIXEL_UNIFORM_FOLDER=%~dp0"
if not exist "%PIXEL_UNIFORM_PYTHON%" (
  echo Bundled Python was not found: %PIXEL_UNIFORM_PYTHON%
  pause
  exit /b 1
)
if not exist "%PIXEL_UNIFORM_SCRIPT%" (
  echo Web launcher was not found: %PIXEL_UNIFORM_SCRIPT%
  pause
  exit /b 1
)
powershell.exe -NoProfile -NonInteractive -Command "$taskArguments = [char]34 + $env:PIXEL_UNIFORM_SCRIPT + [char]34 + ' --open'; Start-Process -FilePath $env:PIXEL_UNIFORM_PYTHON -ArgumentList $taskArguments -WorkingDirectory $env:PIXEL_UNIFORM_FOLDER -WindowStyle Hidden"
if errorlevel 1 (
  echo Could not start the local web application.
  pause
  exit /b 1
)
echo PerfectPixel Uniform: http://127.0.0.1:8768
endlocal
