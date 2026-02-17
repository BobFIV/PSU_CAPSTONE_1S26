$ErrorActionPreference = 'Stop'

$gh = "C:\Program Files\GitHub CLI\gh.exe"

$issueMap = [ordered]@{
    5  = ".github/ISSUE_DRAFTS/callflow/00-epic-callflow-ga-orchestrator.md"
    6  = ".github/ISSUE_DRAFTS/callflow/01-ga-bootstrap-in-resources.md"
    7  = ".github/ISSUE_DRAFTS/callflow/02-orchestrator-bootstrap-and-trigger.md"
    8  = ".github/ISSUE_DRAFTS/callflow/03-ga-cmd-notification-and-execution.md"
    9  = ".github/ISSUE_DRAFTS/callflow/04-ga-data-consumption-mn-restart.md"
    10 = ".github/ISSUE_DRAFTS/callflow/05-ga-register-with-mn.md"
    11 = ".github/ISSUE_DRAFTS/callflow/06-orchestrator-steady-state-updates.md"
    12 = ".github/ISSUE_DRAFTS/callflow/07-e2e-smoke-and-observability.md"
    13 = ".github/ISSUE_DRAFTS/sample-issue-vpn-rpi-localhost.md"
}

function Get-DraftParts {
    param([string]$Path)

    $raw = Get-Content -Path $Path -Raw
    $pattern = "(?s)^# Issue Title\s*\r?\n(?<title>[^\r\n]+)\r?\n(?<body>.*)$"
    $m = [regex]::Match($raw, $pattern)
    if (-not $m.Success) {
        throw "Unable to parse draft file: $Path"
    }

    $title = $m.Groups['title'].Value.Trim()
    $body = $m.Groups['body'].Value.TrimStart("`r", "`n").TrimEnd()
    $body = $body -replace "\r\n", "`n"
    $body = $body -replace "\r", "`n"

    if ($body -notmatch "`n" -and $body -match "\\n") {
        $body = $body -replace "\\n", "`n"
    }

    return [pscustomobject]@{
        Title = $title
        Body  = $body
    }
}

function Write-BodyFile {
    param(
        [string]$Path,
        [string]$Body
    )

    $utf8NoBom = [System.Text.UTF8Encoding]::new($false)
    [System.IO.File]::WriteAllText($Path, $Body, $utf8NoBom)
}

foreach ($entry in $issueMap.GetEnumerator()) {
    $issueNumber = [int]$entry.Key
    $draftRelativePath = [string]$entry.Value
    $draftPath = Join-Path (Get-Location) $draftRelativePath

    if (-not (Test-Path -Path $draftPath -PathType Leaf)) {
        throw "Draft file missing for issue #${issueNumber}: $draftPath"
    }

    $draft = Get-DraftParts -Path $draftPath

    $currentBody = & $gh issue view $issueNumber --json body --jq .body
    $crossLinks = ""
    $crossMatch = [regex]::Match($currentBody, "(?s)<!-- cross-links -->.*$")
    if ($crossMatch.Success) {
        $crossLinks = $crossMatch.Value.Trim()
    }

    $newBody = $draft.Body
    if (-not [string]::IsNullOrWhiteSpace($crossLinks)) {
        $newBody = "$newBody`n`n$crossLinks"
    }

    $tmp = New-TemporaryFile
    Write-BodyFile -Path $tmp -Body $newBody

    & $gh issue edit $issueNumber --title $draft.Title --body-file $tmp | Out-Null

    Remove-Item -Path $tmp -Force
    Write-Host "Reformatted issue #$issueNumber"
}

Write-Host "Issue formatting repair complete."
