$ErrorActionPreference = 'Stop'
$editorCore = Get-Content -Raw -LiteralPath (Join-Path $PSScriptRoot 'T3_NativeAperture154.compute.txt')
$begin = $editorCore.IndexOf('// Shared deterministic core for SelectConnectedOwners154')
$end = $editorCore.IndexOf('StructuredBuffer<uint4> _R25CandidatesRead154;', $begin)
if($begin -lt 0 -or $end -le $begin){throw 'The committed trial does not contain the expected selector core.'}
$work = New-Item -ItemType Directory -Path (Join-Path $env:TEMP ('r25-owner-proof-' + [guid]::NewGuid().ToString('N')))
$editorCore.Substring($begin,$end-$begin) | Set-Content -LiteralPath (Join-Path $work.FullName 'NativeConnectedCore154.hlsl') -Encoding utf8
$vswhere = Join-Path ([Environment]::GetEnvironmentVariable('ProgramFiles(x86)')) 'Microsoft Visual Studio/Installer/vswhere.exe'
$vs = & $vswhere -latest -products '*' -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath
if(!$vs){throw 'Visual Studio C++ build tools are required for this offline check.'}
$vcvars = Join-Path $vs 'VC/Auxiliary/Build/vcvars64.bat'
$source = Join-Path $PSScriptRoot 'OwnerCoreTests.cpp'
$obj = Join-Path $work.FullName 'Core.obj'
$exe = Join-Path $work.FullName 'Core.exe'
$cmd = 'call "'+$vcvars+'" >nul && cl.exe /nologo /EHsc /std:c++17 /O2 /I"'+$work.FullName+'" /Fo"'+$obj+'" /Fe"'+$exe+'" "'+$source+'"'
& cmd.exe /d /c $cmd
if($LASTEXITCODE -ne 0){throw 'C++ test compilation failed.'}
& $exe (Join-Path $PSScriptRoot 'R24OwnerOracle.txt')
if($LASTEXITCODE -ne 0){throw 'The committed selector does not match the preserved C# owner decisions.'}
