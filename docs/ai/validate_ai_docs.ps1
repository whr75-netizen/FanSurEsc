[CmdletBinding()]
param()

$scriptDirectory = Split-Path -Parent $MyInvocation.MyCommand.Path
$repositoryRoot = (Resolve-Path (Join-Path $scriptDirectory '..\..')).Path
$failures = [System.Collections.Generic.List[string]]::new()

function Add-Failure {
    param([string]$Message)
    $failures.Add($Message)
}

$requiredFiles = @(
    'AGENTS.md',
    'docs/ai/CURRENT_STATE.md',
    'docs/ai/GAME_FLOW.md',
    'docs/ai/UNITY_ENGINEERING_PLAYBOOK.md',
    'docs/ai/README.md',
    'extraction_survival_gameplay_contract.md',
    'game_design_document.md',
    'extraction_survival_game_design_dev_plan.md',
    'ai_generation_plan.md',
    'unity_development_progress.md'
)

foreach ($relativePath in $requiredFiles) {
    $absolutePath = Join-Path $repositoryRoot $relativePath
    if (-not (Test-Path -LiteralPath $absolutePath -PathType Leaf)) {
        Add-Failure "Missing routed document: $relativePath"
    }
}

$agentsPath = Join-Path $repositoryRoot 'AGENTS.md'
$statePath = Join-Path $repositoryRoot 'docs/ai/CURRENT_STATE.md'

if (Test-Path -LiteralPath $agentsPath -PathType Leaf) {
    $agentsBytes = (Get-Item -LiteralPath $agentsPath).Length
    if ($agentsBytes -ge 24576) {
        Add-Failure "AGENTS.md is $agentsBytes bytes; it must stay below 24576 bytes."
    }
}

if (Test-Path -LiteralPath $statePath -PathType Leaf) {
    $stateBytes = (Get-Item -LiteralPath $statePath).Length
    if ($stateBytes -ge 12288) {
        Add-Failure "CURRENT_STATE.md is $stateBytes bytes; it must stay below 12288 bytes."
    }

    $stateText = [IO.File]::ReadAllText($statePath)
    $idTableHeaders = [regex]::Matches($stateText, '(?m)^\| ID \|')
    if ($idTableHeaders.Count -ne 2) {
        Add-Failure "CURRENT_STATE must contain exactly two ID data tables; found $($idTableHeaders.Count)."
    }
    else {
        $featureSection = $stateText.Substring($idTableHeaders[0].Index, $idTableHeaders[1].Index - $idTableHeaders[0].Index)
        $gapSection = $stateText.Substring($idTableHeaders[1].Index)

        $declaredFeatureMatches = [regex]::Matches($featureSection, '(?m)^\| \x60(?<id>(?!GAP-)[A-Z][A-Z0-9-]+)\x60 \|')
        $declaredFeatureIds = @($declaredFeatureMatches | ForEach-Object { $_.Groups['id'].Value })
        $featureRowPattern = '(?m)^\| \x60(?<id>(?!GAP-)[A-Z][A-Z0-9-]+)\x60 \| [^|\r\n]+ \| \x60(?<implementation>ACTIVE|PARTIAL|ABSENT|DISABLED)\x60 \| \x60(?<evidence>USER|PLAYER|PLAY|CALL|CODE|UNVERIFIED|BLOCKED)\x60 \| \x60(?<scope>PROTOTYPE|PRODUCTION)\x60 \| [^|\r\n]+ \| [^|\r\n]+ \| [^|\r\n]+ \|[ \t]*\r?$'
        $validFeatureMatches = [regex]::Matches($featureSection, $featureRowPattern)
        $validFeatureIds = @($validFeatureMatches | ForEach-Object { $_.Groups['id'].Value })
        $invalidFeatureIds = @($declaredFeatureIds | Where-Object { $validFeatureIds -notcontains $_ } | Sort-Object -Unique)
        if ($invalidFeatureIds.Count -gt 0) {
            Add-Failure "Invalid CURRENT_STATE feature rows: $($invalidFeatureIds -join ', ')"
        }

        $declaredGapMatches = [regex]::Matches($gapSection, '(?m)^\| \x60(?<id>GAP-[A-Z0-9-]+)\x60 \|')
        $declaredGapIds = @($declaredGapMatches | ForEach-Object { $_.Groups['id'].Value })
        $gapRowPattern = '(?m)^\| \x60(?<id>GAP-[A-Z0-9-]+)\x60 \| \x60(?<status>ABSENT|DECISION)\x60 \| [^|\r\n]+ \| [^|\r\n]+ \|[ \t]*\r?$'
        $validGapMatches = [regex]::Matches($gapSection, $gapRowPattern)
        $validGapIds = @($validGapMatches | ForEach-Object { $_.Groups['id'].Value })
        $invalidGapIds = @($declaredGapIds | Where-Object { $validGapIds -notcontains $_ } | Sort-Object -Unique)
        if ($invalidGapIds.Count -gt 0) {
            Add-Failure "Invalid CURRENT_STATE gap rows: $($invalidGapIds -join ', ')"
        }

        $ids = @($declaredFeatureIds) + @($declaredGapIds)
        $duplicates = @($ids | Group-Object | Where-Object Count -gt 1 | ForEach-Object Name)
        if ($duplicates.Count -gt 0) {
            Add-Failure "Duplicate CURRENT_STATE IDs: $($duplicates -join ', ')"
        }

        $routeLinePattern = '(?m)^\| (?<ids>\x60(?:GAP-)?[A-Z][A-Z0-9-]+\x60(?:, \x60(?:GAP-)?[A-Z][A-Z0-9-]+\x60)*) \| [^|\r\n]+ \|[ \t]*\r?$'
        $routeLineMatches = [regex]::Matches($stateText, $routeLinePattern)
        $routeIds = [System.Collections.Generic.List[string]]::new()
        foreach ($routeLineMatch in $routeLineMatches) {
            $routeIdMatches = [regex]::Matches($routeLineMatch.Groups['ids'].Value, '\x60(?<id>(?:GAP-)?[A-Z][A-Z0-9-]+)\x60')
            foreach ($routeIdMatch in $routeIdMatches) {
                $routeIds.Add($routeIdMatch.Groups['id'].Value)
            }
        }

        $routeDuplicates = @($routeIds | Group-Object | Where-Object Count -gt 1 | ForEach-Object Name)
        if ($routeDuplicates.Count -gt 0) {
            Add-Failure "Duplicate CURRENT_STATE contract routes: $($routeDuplicates -join ', ')"
        }

        $missingRouteIds = @($ids | Where-Object { $routeIds -notcontains $_ } | Sort-Object -Unique)
        if ($missingRouteIds.Count -gt 0) {
            Add-Failure "CURRENT_STATE IDs without contract routes: $($missingRouteIds -join ', ')"
        }

        $orphanRouteIds = @($routeIds | Where-Object { $ids -notcontains $_ } | Sort-Object -Unique)
        if ($orphanRouteIds.Count -gt 0) {
            Add-Failure "CURRENT_STATE contract routes without state rows: $($orphanRouteIds -join ', ')"
        }

        if ($declaredFeatureIds.Count -eq 0) {
            Add-Failure 'CURRENT_STATE has no feature rows.'
        }
        if ($declaredGapIds.Count -eq 0) {
            Add-Failure 'CURRENT_STATE has no gap rows.'
        }
    }
}

$instructionFiles = @(
    'AGENTS.md',
    'docs/ai/CURRENT_STATE.md',
    'docs/ai/GAME_FLOW.md',
    'docs/ai/UNITY_ENGINEERING_PLAYBOOK.md',
    'docs/ai/README.md'
)

foreach ($relativePath in $instructionFiles) {
    $absolutePath = Join-Path $repositoryRoot $relativePath
    if (-not (Test-Path -LiteralPath $absolutePath -PathType Leaf)) {
        continue
    }

    $lines = [IO.File]::ReadAllLines($absolutePath)
    for ($lineIndex = 0; $lineIndex -lt $lines.Length; $lineIndex++) {
        if ($lines[$lineIndex] -match '[ \t]+$') {
            Add-Failure "$relativePath has trailing whitespace at line $($lineIndex + 1)."
        }
    }

    $text = [IO.File]::ReadAllText($absolutePath)
    if ($text.EndsWith("`n`n")) {
        Add-Failure "$relativePath has a blank line at EOF."
    }
}

if (Test-Path -LiteralPath $agentsPath -PathType Leaf) {
    $agentsText = [IO.File]::ReadAllText($agentsPath)
    foreach ($requiredReference in @('docs/ai/CURRENT_STATE.md', 'docs/ai/GAME_FLOW.md', 'docs/ai/UNITY_ENGINEERING_PLAYBOOK.md', 'docs/ai/README.md')) {
        if (-not $agentsText.Contains($requiredReference)) {
            Add-Failure "AGENTS.md does not route to $requiredReference."
        }
    }
}

if ($failures.Count -gt 0) {
    Write-Host 'AI documentation validation failed:'
    foreach ($failure in $failures) {
        Write-Host "- $failure"
    }
    exit 1
}

$finalAgentsBytes = (Get-Item -LiteralPath $agentsPath).Length
$finalStateBytes = (Get-Item -LiteralPath $statePath).Length
Write-Host "AI documentation validation passed. AGENTS=$finalAgentsBytes bytes, CURRENT_STATE=$finalStateBytes bytes."
