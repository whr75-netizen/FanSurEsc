@echo off
setlocal
set "SPRITE_PIPELINE_PYTHON=%USERPROFILE%\.codex\visualizations\2026\09\10\01a08c0e-bbf2-7d10-b1e8-607c2c27f6d3\sprite-gen-trial\venv312\Scripts\python.exe"
if not exist "%SPRITE_PIPELINE_PYTHON%" (
  echo Sprite Pipeline Python runtime was not found.
  pause
  exit /b 1
)
"%SPRITE_PIPELINE_PYTHON%" -X utf8 "%~dp0app.py" --serve --open
