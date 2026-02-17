$ErrorActionPreference = 'Stop'

$ghPath = "C:\Program Files\GitHub CLI\gh.exe"
if (-not (Test-Path $ghPath)) {
    $ghPath = "gh"
}

$repoRoot = Split-Path -Parent $PSScriptRoot
$draftRoot = Join-Path $repoRoot ".github\ISSUE_DRAFTS"

if (-not (Test-Path $draftRoot)) {
    throw "Draft directory not found: $draftRoot"
}

$draftFiles = Get-ChildItem -Path $draftRoot -Recurse -File -Filter *.md |
    Where-Object { $_.Name -notmatch '(^|[-_])template([-_]|\.)|^issue-template\.md$' } |
    Sort-Object FullName
if ($draftFiles.Count -eq 0) {
    Write-Host "No draft files found in $draftRoot"
    exit 0
}

Write-Host "Publishing $($draftFiles.Count) issue drafts..."

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

foreach ($file in $draftFiles) {
    $draft = Get-DraftParts -Path $file.FullName

    $tempBody = [System.IO.Path]::GetTempFileName()
    Write-BodyFile -Path $tempBody -Body $draft.Body

    try {
        $url = & $ghPath issue create --title $draft.Title --body-file $tempBody
        Write-Host "Created: $($draft.Title)"
        Write-Host "  $url"
    }
    finally {
        Remove-Item -Path $tempBody -Force -ErrorAction SilentlyContinue
    }
}

Write-Host "Done."
