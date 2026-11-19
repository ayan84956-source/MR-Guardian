$ErrorActionPreference = "Stop"

$projectRoot = $PSScriptRoot
$python = Join-Path $projectRoot ".venv\Scripts\python.exe"
$cloudflared = Get-Command cloudflared -ErrorAction SilentlyContinue

if (-not (Test-Path $python)) {
    throw "Project Python environment not found at $python. Create the venv and install requirements first."
}

if (-not $cloudflared) {
    throw "cloudflared was not found. Install it with: winget install --id Cloudflare.cloudflared"
}

$logPrefix = Join-Path ([System.IO.Path]::GetTempPath()) "mr-guardian-uvicorn-$PID"
$stdoutLog = "$logPrefix.out.log"
$stderrLog = "$logPrefix.err.log"
$previousPythonPath = $env:PYTHONPATH
$env:PYTHONPATH = Join-Path $projectRoot "src"
$uvicorn = $null
$completed = $false

try {
    $uvicorn = Start-Process `
        -FilePath $python `
        -ArgumentList @(
            "-m", "uvicorn",
            "mr_guardian.api.main:app",
            "--host", "127.0.0.1",
            "--port", "8000"
        ) `
        -WorkingDirectory $projectRoot `
        -RedirectStandardOutput $stdoutLog `
        -RedirectStandardError $stderrLog `
        -PassThru

    $ready = $false
    $lastHealthError = "No response from the health endpoint."
    for ($attempt = 0; $attempt -lt 30; $attempt++) {
        if ($uvicorn.HasExited) {
            throw "Uvicorn exited during startup. See $stderrLog"
        }

        try {
            $health = Invoke-RestMethod `
                -Uri "http://127.0.0.1:8000/health" `
                -TimeoutSec 2
            if ($health.status -eq "healthy") {
                $ready = $true
                break
            }
        }
        catch {
            $lastHealthError = $_.Exception.Message
        }

        Start-Sleep -Seconds 1
    }

    if (-not $ready) {
        throw "MR Guardian did not become healthy within 30 seconds: $lastHealthError See $stderrLog"
    }

    Write-Host "MR Guardian is healthy at http://127.0.0.1:8000"
    Write-Host "Starting a temporary Cloudflare Quick Tunnel. Its public URL changes each run."
    Write-Host "Use the printed https://ethics-evaluated-bone-declare.trycloudflare.com/webhooks/gitlab URL plus /webhooks/gitlab in GitLab."
    Write-Host "Press Ctrl+C to stop the tunnel and local API."
    & $cloudflared.Source tunnel --url "http://127.0.0.1:8000"
    $completed = $true
}
finally {
    if ($uvicorn -and -not $uvicorn.HasExited) {
        Stop-Process -Id $uvicorn.Id
        $uvicorn.WaitForExit()
    }

    $env:PYTHONPATH = $previousPythonPath
    if ($completed) {
        Remove-Item -LiteralPath $stdoutLog, $stderrLog -Force -ErrorAction SilentlyContinue
    }
    else {
        Write-Host "Uvicorn logs, if needed, are at $stdoutLog and $stderrLog"
    }
}
