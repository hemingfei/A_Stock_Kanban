#!/usr/bin/env python3
"""
A股看盘工具 - 跨平台启动脚本
支持 Mac、Windows、Linux
"""

import os
import sys
import subprocess
import time
import signal
import platform
import webbrowser
from pathlib import Path

# 颜色输出（仅在支持的终端）
class Colors:
    if sys.platform.startswith('win'):
        RESET = GREEN = YELLOW = BLUE = RED = ''
    else:
        RESET = '\033[0m'
        GREEN = '\033[92m'
        YELLOW = '\033[93m'
        BLUE = '\033[94m'
        RED = '\033[91m'

def print_info(msg):
    print(f"{Colors.BLUE}[INFO]{Colors.RESET} {msg}")

def print_success(msg):
    print(f"{Colors.GREEN}[SUCCESS]{Colors.RESET} {msg}")

def print_warning(msg):
    print(f"{Colors.YELLOW}[WARNING]{Colors.RESET} {msg}")

def print_error(msg):
    print(f"{Colors.RED}[ERROR]{Colors.RESET} {msg}")

class ProjectLauncher:
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.backend_dir = self.project_root / 'backend'
        self.frontend_dir = self.project_root / 'frontend'
        self.backend_process = None
        self.frontend_process = None

    def check_env_file(self):
        """检查并创建 .env 文件"""
        env_file = self.project_root / '.env'
        env_example = self.project_root / '.env.example'

        if not env_file.exists():
            if env_example.exists():
                import shutil
                shutil.copy(env_example, env_file)
                print_success("已从 .env.example 创建 .env 文件")
            else:
                print_warning(".env.example 不存在，跳过创建")

    def check_backend_dependencies(self):
        """检查后端依赖"""
        venv_dir = self.backend_dir / 'venv'
        if not venv_dir.exists():
            print_info("后端虚拟环境不存在，正在创建...")
            subprocess.run([sys.executable, '-m', 'venv', 'venv'], cwd=self.backend_dir, check=True)
            print_success("虚拟环境创建成功")

        # 检查是否需要安装依赖
        requirements_file = self.backend_dir / 'requirements.txt'
        if requirements_file.exists():
            pip_path = self._get_pip_path()
            print_info("检查后端依赖...")
            result = subprocess.run(
                [str(pip_path), 'install', '-r', 'requirements.txt'],
                cwd=self.backend_dir,
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                print_success("后端依赖已就绪")

    def check_frontend_dependencies(self):
        """检查前端依赖"""
        node_modules = self.frontend_dir / 'node_modules'
        package_json = self.frontend_dir / 'package.json'

        if not package_json.exists():
            print_warning("package.json 不存在，跳过前端依赖检查")
            return

        if not node_modules.exists():
            print_info("前端依赖不存在，正在安装...")
            # 使用临时缓存目录避免权限问题
            env = os.environ.copy()
            env['npm_config_cache'] = str(self.project_root / '.npm-cache')
            subprocess.run(['npm', 'install'], cwd=self.frontend_dir, env=env, check=True)
            print_success("前端依赖安装成功")

    def _get_pip_path(self):
        """获取 pip 路径"""
        venv_dir = self.backend_dir / 'venv'
        if sys.platform.startswith('win'):
            return venv_dir / 'Scripts' / 'pip.exe'
        return venv_dir / 'bin' / 'pip'

    def _get_python_path(self):
        """获取虚拟环境中的 Python 路径"""
        venv_dir = self.backend_dir / 'venv'
        if sys.platform.startswith('win'):
            return venv_dir / 'Scripts' / 'python.exe'
        return venv_dir / 'bin' / 'python'

    def start_backend(self):
        """启动后端服务"""
        print_info("正在启动后端服务...")
        python_path = self._get_python_path()

        env = os.environ.copy()
        env['PYTHONUNBUFFERED'] = '1'

        if sys.platform.startswith('win'):
            creationflags = subprocess.CREATE_NEW_PROCESS_GROUP
            self.backend_process = subprocess.Popen(
                [str(python_path), 'main.py'],
                cwd=self.backend_dir,
                env=env,
                creationflags=creationflags
            )
        else:
            self.backend_process = subprocess.Popen(
                [str(python_path), 'main.py'],
                cwd=self.backend_dir,
                env=env,
                preexec_fn=os.setsid
            )

        # 等待后端启动
        time.sleep(3)
        if self.backend_process.poll() is None:
            print_success("后端服务已启动: http://localhost:8000")
            print_info("API 文档: http://localhost:8000/docs")
            return True
        else:
            print_error("后端启动失败")
            return False

    def start_frontend(self):
        """启动前端服务"""
        print_info("正在启动前端服务...")

        env = os.environ.copy()
        env['npm_config_cache'] = str(self.project_root / '.npm-cache')

        if sys.platform.startswith('win'):
            creationflags = subprocess.CREATE_NEW_PROCESS_GROUP
            self.frontend_process = subprocess.Popen(
                ['npm', 'run', 'dev'],
                cwd=self.frontend_dir,
                env=env,
                creationflags=creationflags
            )
        else:
            self.frontend_process = subprocess.Popen(
                ['npm', 'run', 'dev'],
                cwd=self.frontend_dir,
                env=env,
                preexec_fn=os.setsid
            )

        # 等待前端启动
        time.sleep(5)
        if self.frontend_process.poll() is None:
            print_success("前端服务已启动: http://localhost:3000")
            return True
        else:
            print_error("前端启动失败")
            return False

    def open_browser(self):
        """打开浏览器"""
        try:
            time.sleep(2)
            webbrowser.open('http://localhost:3000')
            print_info("已自动打开浏览器")
        except Exception as e:
            print_warning(f"无法自动打开浏览器: {e}")

    def cleanup(self, signum=None, frame=None):
        """清理子进程"""
        print_info("\n正在停止服务...")

        if self.backend_process and self.backend_process.poll() is None:
            try:
                if sys.platform.startswith('win'):
                    self.backend_process.send_signal(signal.CTRL_BREAK_EVENT)
                else:
                    os.killpg(os.getpgid(self.backend_process.pid), signal.SIGTERM)
                self.backend_process.wait(timeout=5)
                print_success("后端服务已停止")
            except:
                try:
                    self.backend_process.kill()
                except:
                    pass

        if self.frontend_process and self.frontend_process.poll() is None:
            try:
                if sys.platform.startswith('win'):
                    self.frontend_process.send_signal(signal.CTRL_BREAK_EVENT)
                else:
                    os.killpg(os.getpgid(self.frontend_process.pid), signal.SIGTERM)
                self.frontend_process.wait(timeout=5)
                print_success("前端服务已停止")
            except:
                try:
                    self.frontend_process.kill()
                except:
                    pass

        print_info("再见!")
        sys.exit(0)

    def run(self):
        """运行启动器"""
        print("\n" + "="*50)
        print("     A股看盘工具 - 启动器")
        print("="*50 + "\n")

        print_info(f"项目目录: {self.project_root}")
        print_info(f"操作系统: {platform.platform()}")

        # 注册信号处理
        signal.signal(signal.SIGINT, self.cleanup)
        signal.signal(signal.SIGTERM, self.cleanup)
        if sys.platform != 'win32':
            signal.signal(signal.SIGHUP, self.cleanup)

        try:
            self.check_env_file()
            self.check_backend_dependencies()
            self.check_frontend_dependencies()

            if self.start_backend() and self.start_frontend():
                self.open_browser()
                print("\n" + "="*50)
                print_success("服务全部启动成功!")
                print_info("按 Ctrl+C 停止所有服务")
                print("="*50 + "\n")

                # 保持运行
                while True:
                    time.sleep(1)
            else:
                self.cleanup()

        except Exception as e:
            print_error(f"启动失败: {e}")
            import traceback
            traceback.print_exc()
            self.cleanup()

def main():
    launcher = ProjectLauncher()
    launcher.run()

if __name__ == '__main__':
    main()
