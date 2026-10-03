@echo off
setlocal
pushd "%~dp0\..\.."
set "native15Python=C:\Users\JG\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
if not exist "%native15Python%" (
  echo Configured Python runtime was not found.
  popd
  exit /b 1
)
"%native15Python%" -B -c "import sys,uuid;from pathlib import Path;sys.path.insert(0,str(Path('Tools/PerfectPixelUniform').resolve()));from native15_cli import run,HERE,ROOT;result=run(HERE/'native15_recipe.json',ROOT/'docs/artifacts/building37/NativeObject14/appearance-reference.png',ROOT/'LocalOnly/Native15'/uuid.uuid4().hex);print(result);sys.exit(0 if result['action']=='graph_complete' else 2)"
set "native15Exit=%errorlevel%"
popd
exit /b %native15Exit%
