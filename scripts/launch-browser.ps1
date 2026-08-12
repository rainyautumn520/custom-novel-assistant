# AI Novel IDE 浏览器模式启动器
# 用法：双击桌面快捷方式，或在 PowerShell 中执行本脚本

$ErrorActionPreference = 'SilentlyContinue'
$Root = Split-Path -Parent $PSScriptRoot
$ServerDir = Join-Path $Root 'apps\server'
$DesktopDir = Join-Path $Root 'apps\desktop'
$ServerPy = Join-Path $ServerDir '.venv\Scripts\python.exe'
$Node = 'C:\Program Files\nodejs\node.exe'
$ViteJs = Join-Path $Root 'node_modules\vite\bin\vite.js'
$Url = 'http://localhost:5173'

function Test-Port([int]$port) {
    return [bool](Get-NetTCPConnection -State Listen -LocalPort $port -ErrorAction SilentlyContinue)
}

# 1. 后端
if (-not (Test-Port 8000)) {
    if (Test-Path $ServerPy) {
        Start-Process -FilePath $ServerPy -ArgumentList '-m', 'uvicorn', 'app.main:app', '--port', '8000' `
            -WorkingDirectory $ServerDir -WindowStyle Hidden
        Write-Host '[backend] 启动中...' -ForegroundColor Cyan
    } else {
        Write-Host '[backend] 未找到虚拟环境，请先运行 scripts\dev.ps1 安装依赖' -ForegroundColor Yellow
    }
} else {
    Write-Host '[backend] 已在运行' -ForegroundColor Green
}

# 2. 前端
if (-not (Test-Port 5173)) {
    if (Test-Path $Node -and (Test-Path $ViteJs)) {
        Start-Process -FilePath $Node -ArgumentList $ViteJs `
            -WorkingDirectory $DesktopDir -WindowStyle Hidden
        Write-Host '[frontend] 启动中...' -ForegroundColor Cyan
    } else {
        Write-Host '[frontend] 缺少 Node 或 Vite，请先 npm install' -ForegroundColor Yellow
    }
} else {
    Write-Host '[frontend] 已在运行' -ForegroundColor Green
}

# 3. 等待前端就绪后打开浏览器
$ready = $false
for ($i = 0; $i -lt 60; $i++) {
    if (Test-Port 5173) { $ready = $true; break }
    Start-Sleep -Milliseconds 1000
}
if ($ready) {
    Start-Process $Url
    Write-Host "[open] $Url" -ForegroundColor Green
} else {
    Write-Host '[error] 前端未在 60 秒内就绪，请检查 Vite 是否报错' -ForegroundColor Red
}
