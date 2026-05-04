# Builds per-Pi SD-card staging directories from orchestrator-generated
# files + gateway repo + pi-startup repo. Run after provisioning each node
# via the Django orchestrator's /api/provision/host/ endpoint.
#
# Output: PSU_CAPSTONE_1S26/stage/mn1/ and stage/mn2/ each containing the
# 4-file staging set ready to copy onto the SD card's bootfs partition.
#
# Usage:
#   cd C:\Users\jjord\OneDrive\Documents\Captsone\Working\PSU_CAPSTONE_1S26
#   .\build-pi-staging.ps1

$ErrorActionPreference = "Stop"

$ProjectRoot = $PSScriptRoot
if (-not $ProjectRoot) { $ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path }
$GatewayDir = Join-Path $ProjectRoot "gatewayAgent"
$StageRoot  = Join-Path $ProjectRoot "stage"

$firstboot = Join-Path $ProjectRoot "firstboot-setup.sh"
foreach ($f in @($firstboot)) {
    if (-not (Test-Path $f)) {
        Write-Error "Missing required source: $f"
        exit 1
    }
}

$Pis = @(
    @{ Hostname = "mn1"; NodeName = "gw-node-01"; RpiNum = 1 },
    @{ Hostname = "mn2"; NodeName = "gw-node-02"; RpiNum = 2 }
)

foreach ($pi in $Pis) {
    $h     = $pi.Hostname
    $node  = $pi.NodeName
    $rpi   = $pi.RpiNum
    $nodeDir = Join-Path $ProjectRoot "NodeName_$node"
    $wgConf  = Join-Path $nodeDir "wireguard\wg0.conf"
    $envFile = Join-Path $nodeDir ".env.rpi$rpi"
    $stage   = Join-Path $StageRoot $h

    Write-Host ""
    Write-Host "=== Staging $h (node $node) ==="

    if (-not (Test-Path $nodeDir)) {
        Write-Warning "[$h] Node directory missing: $nodeDir"
        continue
    }
    if (-not (Test-Path $wgConf)) {
        Write-Warning "[$h] Missing wg0.conf at $wgConf"
        continue
    }
    if (-not (Test-Path $envFile)) {
        Write-Warning "[$h] Missing $envFile (orchestrator did not generate it)"
        $envFile = Join-Path $GatewayDir ".env.rpi$rpi"
        if (-not (Test-Path $envFile)) {
            Write-Warning "[$h] Fallback env file also missing: $envFile"
            continue
        }
        Write-Host "[$h] Using fallback env file from gatewayAgent: $envFile"
    }

    if (Test-Path $stage) { Remove-Item -Recurse -Force $stage }
    New-Item -ItemType Directory -Force -Path $stage | Out-Null

    Copy-Item $firstboot "$stage\firstboot-setup.sh"
    Copy-Item $wgConf    "$stage\wg0.conf"
    Copy-Item $envFile   "$stage\.env.rpi$rpi"

    # CRLF -> LF on the shell script (bash on Pi will choke on CRLF)
    $shPath = "$stage\firstboot-setup.sh"
    $c = [System.IO.File]::ReadAllText($shPath)
    $c = $c -replace "`r`n", "`n" -replace "`r", "`n"
    [System.IO.File]::WriteAllBytes($shPath, [System.Text.UTF8Encoding]::new($false).GetBytes($c))

    Write-Host "[$h] Staged at: $stage"
    Get-ChildItem $stage | Format-Table Name, Length -AutoSize
}

Write-Host ""
Write-Host "=== Done. Stage dirs under: $StageRoot ==="
Write-Host "Next: copy each stage dir contents onto its Pi SD bootfs partition."
Write-Host "  e.g. for mn1 with SD at E:"
Write-Host '    Copy-Item "C:\Users\jjord\OneDrive\Documents\Captsone\Working\PSU_CAPSTONE_1S26\stage\mn1\*" E:\'
