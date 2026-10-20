param([switch]$Background, [switch]$Studio)

function Test-GatewayCommand {
    param($Process, [string]$ScriptPath, [string]$RootPath, [string]$ConfigPath)
    if (-not $Process -or -not $Process.CommandLine) { return $false }
    $parts = @([regex]::Matches($Process.CommandLine, '"[^"]*"|[^\s]+') | ForEach-Object { $_.Value.Trim('"') })
    if ($parts.Count -lt 6 -or $parts[0] -ne $Process.ExecutablePath) { return $false }
    $scriptMatches = @($parts | Where-Object { $_ -eq $ScriptPath })
    $rootIndex = [Array]::IndexOf($parts, '--root')
    $configIndex = [Array]::IndexOf($parts, '--config')
    return $scriptMatches.Count -eq 1 -and $rootIndex -ge 0 -and $configIndex -ge 0 -and $rootIndex + 1 -lt $parts.Count -and $configIndex + 1 -lt $parts.Count -and $parts[$rootIndex + 1] -eq $RootPath -and $parts[$configIndex + 1] -eq $ConfigPath
}

function Test-GatewayProcessIdentity {
    param($Listener, $Parent, [string]$PythonPath, [string]$BasePythonPath, [string]$ScriptPath, [string]$RootPath, [string]$ConfigPath)
    if (-not (Test-GatewayCommand $Listener $ScriptPath $RootPath $ConfigPath)) { return $false }
    if ($Listener.ExecutablePath -eq $PythonPath) { return $true }
    if (-not $BasePythonPath -or $Listener.ExecutablePath -ne $BasePythonPath -or -not $Parent) { return $false }
    if ($Listener.ParentProcessId -ne $Parent.ProcessId -or $Parent.ExecutablePath -ne $PythonPath) { return $false }
    if (-not (Test-GatewayCommand $Parent $ScriptPath $RootPath $ConfigPath)) { return $false }
    try {
        $childCreated = [datetimeoffset]$Listener.CreationDate
        $parentCreated = [datetimeoffset]$Parent.CreationDate
    } catch { return $false }
    $launchGap = ($childCreated - $parentCreated).TotalSeconds
    return $launchGap -ge 0 -and $launchGap -le 60 -and $childCreated -le [datetimeoffset]::Now.AddSeconds(5)
}

$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'studio-env.ps1')
$gatewayScript = Join-Path $PSScriptRoot 'studio_gateway.py'
$gatewayConfig = Join-Path $studioRoot 'config\gateway.json'
$gatewaySettings = Get-Content -LiteralPath $gatewayConfig -Raw | ConvertFrom-Json
if ($gatewaySettings.host -ne '127.0.0.1') { throw 'Gateway must bind only to 127.0.0.1.' }
$gatewayPort = [int]$gatewaySettings.port
if ($gatewayPort -lt 1 -or $gatewayPort -gt 65535) { throw 'Invalid gateway port.' }
$gatewayPython = Join-Path $studioRoot 'runtime\comfy-venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $gatewayPython -PathType Leaf)) { throw 'Comfy Python environment is missing.' }
$listeners = @(Get-NetTCPConnection -LocalPort $gatewayPort -State Listen -ErrorAction SilentlyContinue)
if ($listeners.Count) {
    $ownerIds = @($listeners.OwningProcess | Select-Object -Unique)
    if ($ownerIds.Count -ne 1) { throw "Port $gatewayPort has ambiguous ownership." }
    $existingGateway = Get-CimInstance Win32_Process -Filter "ProcessId=$($ownerIds[0])"
    $gatewayParent = if ($existingGateway) { Get-CimInstance Win32_Process -Filter "ProcessId=$($existingGateway.ParentProcessId)" }
    $basePython = $null
    $venvConfig = Join-Path $studioRoot 'runtime\comfy-venv\pyvenv.cfg'
    if (Test-Path -LiteralPath $venvConfig -PathType Leaf) {
        $baseSetting = Get-Content -LiteralPath $venvConfig | Where-Object { $_ -match '^executable\s*=' } | Select-Object -First 1
        if ($baseSetting) { $basePython = ($baseSetting -split '=', 2)[1].Trim() }
    }
    if (-not (Test-GatewayProcessIdentity $existingGateway $gatewayParent $gatewayPython $basePython $gatewayScript $studioRoot $gatewayConfig)) {
        throw "Port $gatewayPort is already occupied by another process."
    }
    Write-Output "Reusing Media Studio gateway PID $($existingGateway.ProcessId): http://127.0.0.1:$gatewayPort"
} elseif ($Background -or $Studio) {
    $logDirectory = Join-Path $studioRoot 'logs'
    New-Item -ItemType Directory -Force -Path $logDirectory | Out-Null
    $stamp = Get-Date -Format 'yyyyMMdd-HHmmss-fff'
    $arguments = @('-B', '-X', 'utf8', ('"' + $gatewayScript + '"'), '--root', ('"' + $studioRoot + '"'), '--config', ('"' + $gatewayConfig + '"'))
    $child = Start-Process -FilePath $gatewayPython -ArgumentList $arguments -WorkingDirectory $studioRoot -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $logDirectory "gateway-$stamp.stdout.log") -RedirectStandardError (Join-Path $logDirectory "gateway-$stamp.stderr.log")
    Write-Output "Started Media Studio gateway PID $($child.Id): http://127.0.0.1:$gatewayPort"
} else {
    & $gatewayPython -B -X utf8 $gatewayScript --root $studioRoot --config $gatewayConfig
    if ($LASTEXITCODE -ne 0) { throw "Gateway exited with code $LASTEXITCODE" }
}
if ($Studio) {
    $comfyPort = ([uri]$gatewaySettings.backend_url).Port
    $comfyListeners = @(Get-NetTCPConnection -LocalPort $comfyPort -State Listen -ErrorAction SilentlyContinue)
    if ($comfyListeners.Count) {
        Write-Output "Backend port $comfyPort is already listening; no second Comfy process was launched."
    } else {
        & (Join-Path $PSScriptRoot 'start-comfy.ps1')
    }
}
