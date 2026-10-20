. (Join-Path $PSScriptRoot 'studio-env.ps1')
$pythonExe = Join-Path $studioRoot 'runtime\comfy-venv\Scripts\python.exe'
$comfyRoot = Join-Path $studioRoot 'runtime\ComfyUI'
if (-not (Test-Path -LiteralPath $pythonExe)) { throw 'Comfy Python environment is missing.' }
Write-Output 'Media Studio: http://127.0.0.1:8188  (Ctrl+C stops this process)'
Push-Location $comfyRoot
try {
    & $pythonExe -s main.py --listen 127.0.0.1 --port 8188 --input-directory (Join-Path $studioRoot 'input') --output-directory (Join-Path $studioRoot 'output') --user-directory (Join-Path $studioRoot 'user') --temp-directory (Join-Path $studioRoot 'temp') --models-directory (Join-Path $studioRoot 'models') --disable-auto-launch --offline --enable-assets --fast-disk --disable-pinned-memory --disable-async-offload
    if ($LASTEXITCODE -ne 0) { throw "Comfy exited with code $LASTEXITCODE" }
} finally {
    Pop-Location
}
