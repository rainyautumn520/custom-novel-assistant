# 停止 AI Novel IDE 浏览器模式的开发服务（后端 8000 / 前端 5173）

$ErrorActionPreference = 'SilentlyContinue'
foreach ($port in 8000, 5173) {
    $conns = Get-NetTCPConnection -State Listen -LocalPort $port -ErrorAction SilentlyContinue
    foreach ($conn in $conns) {
        Stop-Process -Id $conn.OwningProcess -Force -ErrorAction SilentlyContinue
        Write-Host "已停止端口 $port 的进程 $($conn.OwningProcess)" -ForegroundColor Yellow
    }
}
Write-Host '开发服务已停止' -ForegroundColor Green
