param(
    [switch]$Public
)

$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $projectRoot

$uvPython = Get-ChildItem "$env:APPDATA\uv\python" -Filter python.exe -Recurse -ErrorAction SilentlyContinue |
Where-Object { $_.FullName -match 'cpython-.+windows' } |
Select-Object -First 1
$python = Get-Command python -ErrorAction SilentlyContinue
if ($null -ne $uvPython) {
    $pythonPath = $uvPython.FullName
}
elseif ($null -ne $python -and $python.Source -notmatch 'WindowsApps') {
    $pythonPath = $python.Source
}
else {
    Write-Error 'Python was not found. Install Python or uv first.'
    exit 1
}

$port = 8000
$lanIp = (Get-NetIPAddress -AddressFamily IPv4 -ErrorAction SilentlyContinue |
    Where-Object { $_.IPAddress -notlike '127.*' -and $_.IPAddress -notlike '169.254.*' -and $_.PrefixOrigin -ne 'WellKnown' } |
    Select-Object -First 1 -ExpandProperty IPAddress)
$appHost = if ($lanIp) { $lanIp } else { $env:COMPUTERNAME }
$appUrl = "http://$appHost`:$port/"
$installUrl = "http://localhost:$port/"
$openUrl = $installUrl
$existing = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
$shouldOpenBrowser = $false
if ($existing) {
    Write-Host "Paddy Mitra is already running at $appUrl" -ForegroundColor Yellow
}
else {
    Write-Host "Starting Paddy Mitra at $appUrl" -ForegroundColor Green
    Start-Process -FilePath $pythonPath -ArgumentList 'server.py' -WorkingDirectory $projectRoot
    $shouldOpenBrowser = $true
    for ($attempt = 0; $attempt -lt 20; $attempt++) {
        Start-Sleep -Milliseconds 250
        $ready = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
        if ($ready) { break }
    }
    if ($null -eq $ready) {
        Write-Error 'The backend did not start. Run server.py directly to see the error.'
        exit 1
    }
}

Write-Host "App URL (same Wi-Fi): $appUrl" -ForegroundColor Green
Write-Host "Install URL (this computer): $installUrl" -ForegroundColor Green
Write-Host "Local IP address: $lanIp" -ForegroundColor Cyan
Write-Host "Computer host name: $env:COMPUTERNAME" -ForegroundColor Cyan
if ($Public) {
    $npx = Get-Command npx.cmd -ErrorAction SilentlyContinue
    if ($null -eq $npx) {
        Write-Error 'Node.js/npx was not found. Install Node.js to use -Public mode.'
        exit 1
    }
    $tunnelLog = Join-Path $projectRoot 'public-tunnel.log'
    $tunnelErrorLog = Join-Path $projectRoot 'public-tunnel-error.log'
    Remove-Item $tunnelLog -Force -ErrorAction SilentlyContinue
    Remove-Item $tunnelErrorLog -Force -ErrorAction SilentlyContinue
    Write-Host 'Starting secure public HTTPS tunnel...' -ForegroundColor Yellow
    $tunnelProcess = Start-Process -FilePath $npx.Source -ArgumentList '--yes localtunnel --port 8000' -WorkingDirectory $projectRoot -RedirectStandardOutput $tunnelLog -RedirectStandardError $tunnelErrorLog -WindowStyle Hidden -PassThru
    $publicUrl = $null
    for ($attempt = 0; $attempt -lt 30; $attempt++) {
        Start-Sleep -Seconds 1
        if (Test-Path $tunnelLog) {
            $match = Select-String -Path $tunnelLog -Pattern 'https://[^\s]+' | Select-Object -First 1
            if ($match) {
                $publicUrl = $match.Matches[0].Value.TrimEnd('.')
                break
            }
        }
    }
    if ($null -eq $publicUrl) {
        if ($tunnelProcess.HasExited) {
            throw 'The public tunnel stopped before creating a URL. Check public-tunnel.log and public-tunnel-error.log.'
        }
        throw 'The public tunnel did not start. Check public-tunnel.log.'
    }
    $openUrl = "$publicUrl/"
    Start-Process $openUrl
    Write-Host "Public app URL (any internet): $openUrl" -ForegroundColor Green
    try {
        $publicIp = (Invoke-RestMethod -Uri 'https://api.ipify.org?format=text' -TimeoutSec 5).Trim()
        Write-Host "Public network IP: $publicIp" -ForegroundColor Cyan
        Write-Host 'Note: the public network IP alone does not open the app unless router port forwarding is configured.' -ForegroundColor DarkYellow
    }
    catch {
        Write-Host 'Public network IP could not be detected.' -ForegroundColor DarkYellow
    }
    Write-Host 'Keep this PowerShell session and tunnel process running while sharing the URL.' -ForegroundColor Yellow
}
if ($shouldOpenBrowser -and -not $Public) {
    Start-Process $openUrl
}
Write-Host 'Login page opened. Demo account: ravi / paddy123' -ForegroundColor Cyan
