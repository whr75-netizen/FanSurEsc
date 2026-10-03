@echo off
setlocal
pushd "%~dp0\..\.."
set "native14Python=C:\Users\JG\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
if not exist "%native14Python%" (
  echo Configured Python runtime was not found.
  popd
  exit /b 1
)
"%native14Python%" -B -c "import sys,uuid;from pathlib import Path;sys.path.insert(0,str(Path('Tools/PerfectPixelUniform').resolve()));from native14_cli import run,HERE,ROOT;result=run(HERE/'native14_recipe.json',ROOT/'docs/artifacts/building37/NativeObject14/appearance-reference.png',ROOT/'LocalOnly/Native14'/uuid.uuid4().hex);print(result);sys.exit(0 if result['action']=='graph_complete' else 2)"
set "native14Exit=%errorlevel%"
popd
exit /b %native14Exit%
