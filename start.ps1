# A股看盘工具 - PowerShell 启动脚本
# 适用于 Windows 10/11

param(
    [switch]$NoBrowser
)

$ErrorActionPreference = "Stop"

# 颜色输出函数
function Write-Info { param($Message) Write-Host "[INFO] $Message" -ForegroundColor Cyan }
function Write-Success { param($Message) Write-Host "[SUCCESS] $Message" -ForegroundColor Green }
function Write-Warning { param($Message) Write-Host "[WARNING] $Message" -ForegroundColor Yellow }
function Write-Error { param($Message) Write-Host "[ERROR] $Message" -ForegroundColor Red }

# 获取项目根目录
$ProjectRoot = $PSScriptRoot
$BackendDir = Join-Path $ProjectRoot "backend"
$FrontendDir = Join-Path $ProjectRoot "frontend"

# 后台任务跟踪
$BackendJob = $null
$FrontendJob = $null

# 清理函数
function Cleanup {
    Write-Host ""
    Write-Info "正在停止服务..."

    if ($BackendJob) {
        Stop-Job -Job $BackendJob -ErrorAction SilentlyContinue
        Remove-Job -Job $BackendJob -Force -ErrorAction SilentlyContinue
        Write-Success "后端服务已停止"
    }

    if ($FrontendJob) {
        Stop-Job -Job $FrontendJob -ErrorAction SilentlyContinue
        Remove-Job -Job $FrontendJob -Force -ErrorAction SilentlyContinue
        Write-Success "前端服务已停止"
    }

    Write-Info "再见!"
    exit 0
}

# 注册 Ctrl+C 处理
Register-EngineEvent -SourceIdentifier PowerShell.Exiting -Action { Cleanup } | Out-Null

# 主程序
try {
    Write-Host ""
    Write-Host "==================================================" -ForegroundColor Magenta
    Write-Host "     A股看盘工具 - 启动器" -ForegroundColor Magenta
    Write-Host "==================================================" -ForegroundColor Magenta
    Write-Host ""

    Write-Info "项目目录: $ProjectRoot"
    Write-Info "操作系统: $([Environment]::OSVersion.VersionString)"

    # 检查 .env 文件
    $EnvFile = Join-Path $ProjectRoot ".env"
    $EnvExample = Join-Path $ProjectRoot ".env.example"

    if (-not (Test-Path $EnvFile)) {
        if (Test-Path $EnvExample) {
            Copy-Item $EnvExample $EnvFile
            Write-Success "已从 .env.example 创建 .env 文件"
        } else {
            Write-Warning ".env.example 不存在，跳过创建"
        }
    }

    # 检查后端虚拟环境
    $VenvDir = Join-Path $BackendDir "venv"
    if (-not (Test-Path $VenvDir)) {
        Write-Info "后端虚拟环境不存在，正在创建..."
        Push-Location $BackendDir
        python -m venv venv
        Pop-Location
        Write-Success "虚拟环境创建成功"
    }

    # 安装后端依赖
    $RequirementsFile = Join-Path $BackendDir "requirements.txt"
    if (Test-Path $RequirementsFile) {
        Write-Info "检查后端依赖..."
        $PythonPath = Join-Path $VenvDir "Scripts\python.exe"
        $PipPath = Join-Path $VenvDir "Scripts\pip.exe"
        & $PipPath install -r $RequirementsFile -q
        Write-Success "后端依赖已就绪"
    }

    # 检查前端依赖
    $NodeModules = Join-Path $FrontendDir "node_modules"
    $PackageJson = Join-Path $FrontendDir "package.json"

    if (-not (Test-Path $NodeModules) -and (Test-Path $PackageJson)) {
        Write-Info "前端依赖不存在，正在安装..."
        Push-Location $FrontendDir
        $env:npm_config_cache = Join-Path $ProjectRoot ".npm-cache"
        npm install
        Pop-Location
        Write-Success "前端依赖安装成功"
    }

    # 启动后端
    Write-Info "正在启动后端服务..."
    $PythonPath = Join-Path $VenvDir "Scripts\python.exe"
    $BackendScript = Join-Path $BackendDir "main.py"

    $BackendJob = Start-Job -ScriptBlock {
        param($PythonPath, $BackendScript, $BackendDir)
        Set-Location $BackendDir
        & $PythonPath $BackendScript
    } -ArgumentList $PythonPath, $BackendScript, $BackendDir

    # 等待后端启动
    Start-Sleep -Seconds 3

    # 检查后端状态
    if ($BackendJob.State -eq "Failed") {
        Write-Error "后端启动失败"
        Receive-Job -Job $BackendJob
        Cleanup
    }

    Write-Success "后端服务已启动: http://localhost:8000"
    Write-Info "API 文档: http://localhost:8000/docs"

    # 启动前端
    Write-Info "正在启动前端服务..."
    $FrontendJob = Start-Job -ScriptBlock {
        param($FrontendDir, $ProjectRoot)
        Set-Location $FrontendDir
        $env:npm_config_cache = Join-Path $ProjectRoot ".npm-cache"
        npm run dev
    } -ArgumentList $FrontendDir, $ProjectRoot

    # 等待前端启动
    Start-Sleep -Seconds 5

    # 检查前端状态
    if ($FrontendJob.State -eq "Failed") {
        Write-Error "前端启动失败"
        Receive-Job -Job $FrontendJob
        Cleanup
    }

    Write-Success "前端服务已启动: http://localhost:3000"

    # 打开浏览器
    if (-not $NoBrowser) {
        Start-Sleep -Seconds 2
        Start-Process "http://localhost:3000"
        Write-Info "已自动打开浏览器"
    }

    Write-Host ""
    Write-Host "==================================================" -ForegroundColor Magenta
    Write-Success "服务全部启动成功!"
    Write-Info "按 Ctrl+C 停止所有服务"
    Write-Host "==================================================" -ForegroundColor Magenta
    Write-Host ""

    # 显示日志
    Write-Info "显示服务日志 (按 Ctrl+C 停止):"
    Write-Host ""

    # 保持运行并显示输出
    while ($true) {
        if ($BackendJob -and $BackendJob.HasMoreData) {
            Receive-Job -Job $BackendJob
        }
        if ($FrontendJob -and $FrontendJob.HasMoreData) {
            Receive-Job -Job $FrontendJob
        }

        # 检查任务状态
        if ($BackendJob -and $BackendJob.State -ne "Running") {
            Write-Warning "后端服务已停止"
        }
        if ($FrontendJob -and $FrontendJob.State -ne "Running") {
            Write-Warning "前端服务已停止"
        }

        Start-Sleep -Seconds 1
    }

} catch {
    Write-Error "启动失败: $_"
    Write-Error $_.ScriptStackTrace
    Cleanup
}
