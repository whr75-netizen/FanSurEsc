$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = New-Object System.Text.UTF8Encoding($false)
$taskRoot = $PSScriptRoot
# Plain .NET compiler only: no Unity assemblies, API, graphics device or GPU compiler.
Add-Type -Path @(
    (Join-Path $taskRoot 'candidate\SourcePalette58.cs'),
    (Join-Path $taskRoot 'ResolvedRegionInput.cs'),
    (Join-Path $taskRoot 'CpuTests.cs')
) -ReferencedAssemblies @('System.dll','System.Core.dll','System.Web.Extensions.dll')
[RegionBridgeTests]::Run((Join-Path $taskRoot 'FIXTURE58.json'))
