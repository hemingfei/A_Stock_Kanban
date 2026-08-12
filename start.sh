#!/bin/bash
# A股看盘工具 - Mac/Linux 启动脚本

set -e

# 颜色输出
RED='\033[91m'
GREEN='\033[92m'
YELLOW='\033[93m'
BLUE='\033[94m'
RESET='\033[0m'

print_info() {
    echo -e "${BLUE}[INFO]${RESET} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${RESET} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${RESET} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${RESET} $1"
}

# 获取项目根目录
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$PROJECT_ROOT/backend"
FRONTEND_DIR="$PROJECT_ROOT/frontend"

# 进程 PID 文件
BACKEND_PID="$PROJECT_ROOT/.backend.pid"
FRONTEND_PID="$PROJECT_ROOT/.frontend.pid"

# 清理函数
cleanup() {
    echo ""
    print_info "正在停止服务..."

    if [ -f "$BACKEND_PID" ]; then
        PID=$(cat "$BACKEND_PID" 2>/dev/null || true)
        if [ -n "$PID" ] && kill -0 "$PID" 2>/dev/null; then
            kill -TERM "$PID" 2>/dev/null || true
            wait "$PID" 2>/dev/null || true
            print_success "后端服务已停止"
        fi
        rm -f "$BACKEND_PID"
    fi

    if [ -f "$FRONTEND_PID" ]; then
        PID=$(cat "$FRONTEND_PID" 2>/dev/null || true)
        if [ -n "$PID" ] && kill -0 "$PID" 2>/dev/null; then
            kill -TERM "$PID" 2>/dev/null || true
            wait "$PID" 2>/dev/null || true
            print_success "前端服务已停止"
        fi
        rm -f "$FRONTEND_PID"
    fi

    print_info "再见!"
    exit 0
}

# 检查 .env 文件
check_env() {
    if [ ! -f "$PROJECT_ROOT/.env" ]; then
        if [ -f "$PROJECT_ROOT/.env.example" ]; then
            cp "$PROJECT_ROOT/.env.example" "$PROJECT_ROOT/.env"
            print_success "已从 .env.example 创建 .env 文件"
        else
            print_warning ".env.example 不存在，跳过创建"
        fi
    fi
}

# 检查后端依赖
check_backend() {
    if [ ! -d "$BACKEND_DIR/venv" ]; then
        print_info "后端虚拟环境不存在，正在创建..."
        cd "$BACKEND_DIR"
        python3 -m venv venv
        print_success "虚拟环境创建成功"
    fi

    if [ -f "$BACKEND_DIR/requirements.txt" ]; then
        print_info "检查后端依赖..."
        cd "$BACKEND_DIR"
        source venv/bin/activate
        pip install -r requirements.txt -q
        print_success "后端依赖已就绪"
    fi
}

# 检查前端依赖
check_frontend() {
    if [ ! -d "$FRONTEND_DIR/node_modules" ] && [ -f "$FRONTEND_DIR/package.json" ]; then
        print_info "前端依赖不存在，正在安装..."
        cd "$FRONTEND_DIR"
        npm install --cache "$PROJECT_ROOT/.npm-cache"
        print_success "前端依赖安装成功"
    fi
}

# 启动后端
start_backend() {
    print_info "正在启动后端服务..."
    cd "$BACKEND_DIR"
    source venv/bin/activate

    # 启动后端
    python3 main.py &
    BACKEND_PID_VAL=$!
    echo "$BACKEND_PID_VAL" > "$BACKEND_PID"

    # 等待启动
    sleep 3

    if kill -0 "$BACKEND_PID_VAL" 2>/dev/null; then
        print_success "后端服务已启动: http://localhost:8000"
        print_info "API 文档: http://localhost:8000/docs"
        return 0
    else
        print_error "后端启动失败"
        return 1
    fi
}

# 启动前端
start_frontend() {
    print_info "正在启动前端服务..."
    cd "$FRONTEND_DIR"

    # 启动前端
    npm run dev -- --host 2>&1 &
    FRONTEND_PID_VAL=$!
    echo "$FRONTEND_PID_VAL" > "$FRONTEND_PID"

    # 等待启动
    sleep 5

    if kill -0 "$FRONTEND_PID_VAL" 2>/dev/null; then
        print_success "前端服务已启动: http://localhost:3000"
        return 0
    else
        print_error "前端启动失败"
        return 1
    fi
}

# 打开浏览器
open_browser() {
    sleep 2
    if command -v open &> /dev/null; then
        open "http://localhost:3000"
    elif command -v xdg-open &> /dev/null; then
        xdg-open "http://localhost:3000"
    else
        print_warning "无法自动打开浏览器，请手动访问 http://localhost:3000"
        return
    fi
    print_info "已自动打开浏览器"
}

# 主函数
main() {
    echo ""
    echo "=================================================="
    echo "     A股看盘工具 - 启动器"
    echo "=================================================="
    echo ""

    print_info "项目目录: $PROJECT_ROOT"
    print_info "操作系统: $(uname -s)"

    # 注册清理函数
    trap cleanup SIGINT SIGTERM EXIT

    # 检查并创建 .env
    check_env

    # 检查依赖
    check_backend
    check_frontend

    # 启动服务
    if start_backend && start_frontend; then
        open_browser

        echo ""
        echo "=================================================="
        print_success "服务全部启动成功!"
        print_info "按 Ctrl+C 停止所有服务"
        echo "=================================================="
        echo ""

        # 保持运行
        wait
    else
        cleanup
    fi
}

# 运行主函数
main
