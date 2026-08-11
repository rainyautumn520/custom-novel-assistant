# AI Novel IDE 一键启动（开发模式）
# 用法：powershell -ExecutionPolicy Bypass -File scripts/dev.ps1

$Root = Split-Path -Parent $PSScriptRoot
$Server = Join-Path $Root 'apps\server'

if (-not (Test-Path (Join-Path $Server '.venv'))) {
    Write-Host '[server] 创建虚拟环境并安装依赖...' -ForegroundColor Cyan
    Push-Location $Server
    python -m venv .venv
    .\.venv\Scripts\python -m pip install -r requirements.txt
    Pop-Location
}

Write-Host '[server] 启动 FastAPI (http://localhost:8000)' -ForegroundColor Cyan
Push-Location $Server
$server = Start-Process -FilePath '.\.venv\Scripts\python.exe' `
    -ArgumentList '-m', 'uvicorn', 'app.main:app', '--reload', '--port', '8000' `
    -PassThru -WindowStyle Hidden
Pop-Location

Write-Host '[desktop] 启动 Electron + Vite' -ForegroundColor Cyan
Push-Location $Root
npm run electron:dev -w @ai-novel-ide/desktop
Pop-Location

Write-Host '[server] 停止后端...' -ForegroundColor Yellow
Stop-Process -Id $server.Id -Force -ErrorAction SilentlyContinue
