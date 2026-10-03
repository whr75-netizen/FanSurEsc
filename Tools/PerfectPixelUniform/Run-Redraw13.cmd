@echo off
setlocal
set "TASK_PYTHON=%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
if not exist "%TASK_PYTHON%" (
  echo Bundled Python was not found. See REDRAW13.md.
  exit /b 1
)
cd /d "%~dp0..\.."
"%TASK_PYTHON%" -B "%~dp0redraw13_cli.py" %*
exit /b %errorlevel%
