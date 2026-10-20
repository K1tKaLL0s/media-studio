$ErrorActionPreference = 'Stop'
$studioRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$env:MEDIA_STUDIO_ROOT = $studioRoot
$studioCachePaths = @{
    TEMP = 'temp'; TMP = 'temp'; TMPDIR = 'temp'
    HF_HOME = 'cache\huggingface'; HF_HUB_CACHE = 'cache\huggingface\hub'
    TORCH_HOME = 'cache\torch'; XDG_CACHE_HOME = 'cache'
    PIP_CACHE_DIR = 'cache\pip'; PYTHONPYCACHEPREFIX = 'cache\pycache'
    CUDA_CACHE_PATH = 'cache\cuda'; TORCHINDUCTOR_CACHE_DIR = 'cache\inductor'
    TRITON_CACHE_DIR = 'cache\triton'; MPLCONFIGDIR = 'cache\matplotlib'
    NUMBA_CACHE_DIR = 'cache\numba'; npm_config_cache = 'cache\npm'
    PLAYWRIGHT_BROWSERS_PATH = 'cache\playwright'
}
foreach ($entry in $studioCachePaths.GetEnumerator()) {
    $cachePath = Join-Path $studioRoot $entry.Value
    New-Item -ItemType Directory -Force -Path $cachePath | Out-Null
    [Environment]::SetEnvironmentVariable($entry.Key, $cachePath, 'Process')
}
$env:COMFY_WHERE = 'local'
$env:PYTHONNOUSERSITE = '1'
$env:PYTHONUTF8 = '1'
$env:PYTHONIOENCODING = 'utf-8'
$env:HF_HUB_DISABLE_TELEMETRY = '1'
$env:DO_NOT_TRACK = '1'
$runtimeConfig = $env:MEDIA_STUDIO_RUNTIME_CONFIG
if (-not $runtimeConfig) { $runtimeConfig = Join-Path $studioRoot 'config\runtime-paths.json' }
$runtimeKeys = @{
    tts_python = @('MEDIA_STUDIO_TTS_PYTHON')
    pv_python = @('MEDIA_STUDIO_PV_PYTHON', 'PV_PYTHON')
    node = @('MEDIA_STUDIO_NODE', 'NODE')
    ffmpeg = @('MEDIA_STUDIO_FFMPEG', 'FFMPEG')
    ffprobe = @('MEDIA_STUDIO_FFPROBE', 'FFPROBE')
    browser_channel = @('MEDIA_STUDIO_BROWSER_CHANNEL', 'BROWSER_CHANNEL')
    browser_angle = @('MEDIA_STUDIO_BROWSER_ANGLE', 'BROWSER_ANGLE')
}
if (Test-Path -LiteralPath $runtimeConfig -PathType Leaf) {
    $runtimeSettings = Get-Content -LiteralPath $runtimeConfig -Raw | ConvertFrom-Json
    if ($runtimeSettings -isnot [pscustomobject]) { throw 'Runtime configuration must be a JSON object.' }
    foreach ($runtimeKey in $runtimeKeys.Keys) {
        $property = $runtimeSettings.PSObject.Properties[$runtimeKey]
        if ($null -ne $property) {
            if ($property.Value -isnot [string]) { throw "Runtime setting must be a string: $runtimeKey" }
            $alreadySet = $false
            foreach ($variableName in $runtimeKeys[$runtimeKey]) {
                if ($null -ne [Environment]::GetEnvironmentVariable($variableName, 'Process')) { $alreadySet = $true }
            }
            if (-not $alreadySet) { [Environment]::SetEnvironmentVariable($runtimeKeys[$runtimeKey][0], $property.Value, 'Process') }
        }
    }
}
if (-not $env:FFMPEG) {
    $env:FFMPEG = if ($env:MEDIA_STUDIO_FFMPEG) { $env:MEDIA_STUDIO_FFMPEG } else { Join-Path $studioRoot 'runtime\ffmpeg\bin\ffmpeg.exe' }
}
if (-not $env:FFPROBE) {
    $env:FFPROBE = if ($env:MEDIA_STUDIO_FFPROBE) { $env:MEDIA_STUDIO_FFPROBE } else { Join-Path $studioRoot 'runtime\ffmpeg\bin\ffprobe.exe' }
}
$env:JIZURA_DIR = Join-Path $studioRoot 'runtime\JIZURA'
$env:PATH = (Split-Path -Parent $env:FFMPEG) + ';' + $env:PATH
