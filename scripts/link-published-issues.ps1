$ErrorActionPreference = 'Stop'

$gh = "C:\Program Files\GitHub CLI\gh.exe"

function Write-BodyFile {
    param(
        [string]$Path,
        [string]$Body
    )

    $utf8NoBom = [System.Text.UTF8Encoding]::new($false)
    [System.IO.File]::WriteAllText($Path, $Body, $utf8NoBom)
}

function Append-CrossLinks {
    param(
        [int]$IssueNumber,
        [string]$SectionMarkdown
    )

    $body = & $gh issue view $IssueNumber --json body --jq .body
    if ($body -match '<!-- cross-links -->') {
        Write-Host "Issue #$IssueNumber already has cross-links; skipping"
        return
    }

    $newBody = "$body`n`n<!-- cross-links -->`n$SectionMarkdown"
    $tmp = New-TemporaryFile
    Write-BodyFile -Path $tmp -Body $newBody
    & $gh issue edit $IssueNumber --body-file $tmp | Out-Null
    Remove-Item $tmp -Force
    Write-Host "Updated issue #$IssueNumber"
}

$epicSection = @"
## Linked Child Issues
- [ ] #6 GA: Bootstrap IN-CSE resources for gateway
- [ ] #7 Orchestrator: Bootstrap AE and write initial cmd/data content
- [ ] #8 GA: Handle cmd notification and execute workflow
- [ ] #9 GA: Consume data content, update config, restart MN-CSE
- [ ] #10 GA: Register with MN-CSE after restart
- [ ] #11 Orchestrator: Steady-state gateway config updates via data resource
- [ ] #12 E2E: Validate callflow and add observability for GA + Orchestrator

## Related
- #13 Run WireGuard VPN on rPI and localhost
"@
Append-CrossLinks -IssueNumber 5 -SectionMarkdown $epicSection

Append-CrossLinks -IssueNumber 6 -SectionMarkdown @"
## Cross-Links
- Parent Epic: #5
- Blocks: #7, #8
"@

Append-CrossLinks -IssueNumber 7 -SectionMarkdown @"
## Cross-Links
- Parent Epic: #5
- Depends on: #6
- Blocks: #8, #11
"@

Append-CrossLinks -IssueNumber 8 -SectionMarkdown @"
## Cross-Links
- Parent Epic: #5
- Depends on: #6, #7
- Blocks: #9
"@

Append-CrossLinks -IssueNumber 9 -SectionMarkdown @"
## Cross-Links
- Parent Epic: #5
- Depends on: #8
- Blocks: #10, #11, #12
"@

Append-CrossLinks -IssueNumber 10 -SectionMarkdown @"
## Cross-Links
- Parent Epic: #5
- Depends on: #9
- Blocks: #12
"@

Append-CrossLinks -IssueNumber 11 -SectionMarkdown @"
## Cross-Links
- Parent Epic: #5
- Depends on: #7, #9
- Blocks: #12
"@

Append-CrossLinks -IssueNumber 12 -SectionMarkdown @"
## Cross-Links
- Parent Epic: #5
- Depends on: #6, #7, #8, #9, #10, #11
"@

Append-CrossLinks -IssueNumber 13 -SectionMarkdown @"
## Cross-Links
- Related Epic: #5
"@

Write-Host "Cross-linking complete."
