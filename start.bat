@echo off
chcp 65001 >nul
title A股看盘工具 - 启动器

setlocal enabledelayedexpansion

REM 设置颜色输出
for /F %%a in ('echo prompt $E ^| cmd') do set "ESC=%%a"
set "GREEN=%ESC%[92m"
set "YELLOW=%ESC%[93m"
set "BLUE=%ESC%[94m"
set "RED=%ESC%[91m"
set "RESET=%ESC%[0m"

REM 获取项目根目录
set "PROJECT_ROOT=%~dp0"
set "BACKEND_DIR=%PROJECT_ROOT%backend"
set "FRONTEND_DIR=%PROJECT_ROOT%frontend"

REM PID 文件
set "BACKEND_PID=%PROJECT_ROOT%.backend.pid"
set "FRONTEND_PID=%PROJECT_ROOT%.frontend.pid"

echo.
echo ==================================================
echo      A股看盘工具 - 启动器
echo ==================================================
echo.

echo [INFO] 项目目录: %PROJECT_ROOT%
echo [INFO] 操作系统: Windows

REM 检查 .env 文件
if not exist "%PROJECT_ROOT%.env" (
    if exist "%PROJECT_ROOT%.env.example" (
        copy "%PROJECT_ROOT%.env.example" "%PROJECT_ROOT%.env" >nul
        echo %GREEN%[SUCCESS]%RESET% 已从 .env.example 创建 .env 文件
    ) else (
        echo %YELLOW%[WARNING]%RESET% .env.example 不存在，跳过创建
    )
)

REM 检查后端虚拟环境
if not exist "%BACKEND_DIR%\venv" (
    echo [INFO] 后端虚拟环境不存在，正在创建...
    cd /d "%BACKEND_DIR%"
    python -m venv venv
    echo %GREEN%[SUCCESS]%RESET% 虚拟环境创建成功
)

REM 安装后端依赖
if exist "%BACKEND_DIR%\requirements.txt" (
    echo [INFO] 检查后端依赖...
    cd /d "%BACKEND_DIR%"
    call venv\Scripts\activate.bat
    pip install -r requirements.txt -q
    echo %GREEN%[SUCCESS]%RESET% 后端依赖已就绪
)

REM 检查前端依赖
if not exist "%FRONTEND_DIR%\node_modules" (
    if exist "%FRONTEND_DIR%\package.json" (
        echo [INFO] 前端依赖不存在，正在安装...
        cd /d "%FRONTEND_DIR%"
        set "npm_config_cache=%PROJECT_ROOT%.npm-cache"
        call npm install
        echo %GREEN%[SUCCESS]%RESET% 前端依赖安装成功
    )
)

REM 启动后端
echo [INFO] 正在启动后端服务...
cd /d "%BACKEND_DIR%"
call venv\Scripts\activate.bat
start "A股看盘-后端" python main.py

REM 等待后端启动
timeout /t 3 /nobreak >nul

REM 启动前端
echo [INFO] 正在启动前端服务...
cd /d "%FRONTEND_DIR%"
set "npm_config_cache=%PROJECT_ROOT%.npm-cache"
start "A股看盘-前端" npm run dev

REM 等待前端启动
timeout /t 5 /nobreak >nul

REM 打开浏览器
echo [INFO] 正在打开浏览器...
timeout /t 2 /nobreak >nul
start http://localhost:3000
echo %GREEN%[SUCCESS]%RESET% 已自动打开浏览器

echo.
echo ==================================================
echo %GREEN%[SUCCESS]%RESET% 服务全部启动成功!
echo [INFO] 前端: http://localhost:3000
echo [INFO] 后端: http://localhost:8000
echo [INFO] API文档: http://localhost:8000/docs
echo.
echo [INFO] 关闭此窗口不会停止服务
echo [INFO] 如需停止，请关闭弹出的后端和前端窗口
echo ==================================================
echo.

REM 保持窗口打开，让用户看到信息
echo 按任意键关闭此窗口（服务将继续运行）...
pause >nul
