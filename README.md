# A股看盘工具

一个支持多用户、自定义板块、实时行情的A股看盘网页工具。

## 技术栈

- **后端**: FastAPI + SQLAlchemy + Redis
- **前端**: React + TypeScript + Ant Design
- **数据源**: AkShare (免费开源)
- **部署**: Docker Compose

## 快速启动

### 方式一：使用启动脚本（推荐）

**Mac / Linux:**
```bash
# 方式 1: Python 脚本（推荐，跨平台）
python3 start.py

# 方式 2: Shell 脚本
./start.sh
```

**Windows:**
```cmd
# 方式 1: Python 脚本（推荐，跨平台）
python start.py

# 方式 2: Batch 脚本（双击运行）
start.bat

# 方式 3: PowerShell 脚本
powershell -ExecutionPolicy Bypass -File start.ps1
```

### 方式二：手动启动

#### 1. 配置环境
```bash
cp .env.example .env
```

#### 2. 启动后端
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

#### 3. 启动前端
```bash
cd frontend
npm install
npm run dev
```

### Docker 部署

```bash
cp .env.example .env
# 编辑 .env 设置生产环境变量
docker-compose up -d
```

## 访问地址

启动成功后，访问以下地址：

- **前端界面**: http://localhost:3000/
- **后端 API**: http://localhost:8000/
- **API 文档**: http://localhost:8000/docs

## 功能特性

- [x] 用户注册/登录
- [x] 自定义板块管理
- [x] 个股添加/删除
- [x] 实时行情刷新
- [x] K线图展示
- [x] 响应式设计
- [ ] 更多功能开发中...

## License

MIT
