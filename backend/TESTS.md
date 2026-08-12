# 测试说明

本项目包含完整的后端 API 测试覆盖。

## 测试文件

```
tests/
├── conftest.py              # 测试配置和 fixtures
├── test_auth.py             # 认证模块测试
├── test_boards.py           # 看板管理测试
├── test_stocks.py           # 股票管理测试
├── test_quotes.py           # 行情接口测试
├── test_settings.py         # 用户设置测试
├── test_health.py           # 健康检查测试
└── test_boundary_cases.py   # 边界情况测试
```

## 运行测试

### 安装依赖

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 运行所有测试

```bash
pytest
```

### 运行特定测试文件

```bash
pytest tests/test_auth.py -v
```

### 运行并显示详细输出

```bash
pytest -v
```

### 生成覆盖率报告

```bash
pytest --cov=app --cov-report=html
# 查看 htmlcov/index.html
```

## 测试覆盖范围

### 认证模块 (test_auth.py)
- ✅ 用户注册
- ✅ 重复用户名注册失败
- ✅ 用户登录
- ✅ 无效凭证登录失败
- ✅ 获取当前用户信息
- ✅ 用户名边界长度测试
- ✅ 密码边界长度测试
- ✅ Token 刷新功能
- ✅ Token 黑名单测试
- ✅ 登出功能
- ✅ 审计日志记录

### 看板管理模块 (test_boards.py)
- ✅ 创建看板 - 正常流程
- ✅ 创建看板 - 空名称验证
- ✅ 创建看板 - 名称超长验证
- ✅ 获取所有看板 - 空列表
- ✅ 获取所有看板 - 有数据
- ✅ 获取单个看板 - 存在
- ✅ 获取单个看板 - 不存在
- ✅ 获取单个看板 - 无权限访问
- ✅ 更新看板 - 正常更新
- ✅ 更新看板 - 空名称
- ✅ 更新看板 - 不存在
- ✅ 删除看板 - 正常删除
- ✅ 删除看板 - 不存在
- ✅ 删除看板 - 无权限
- ✅ 看板排序 - 正常排序
- ✅ 看板排序 - 包含不存在的 ID
- ✅ 看板排序 - 空列表
- ✅ 看板创建时的排序顺序
- ✅ include_stocks 参数

### 股票管理模块 (test_stocks.py)
- ✅ 添加股票到看板 - 正常流程
- ✅ 添加股票 - 代码超长
- ✅ 添加股票 - 名称超长
- ✅ 添加股票 - 重复添加
- ✅ 添加股票 - 看板不存在
- ✅ 添加股票 - 无权限看板
- ✅ 获取看板股票 - 空列表
- ✅ 获取看板股票 - 有数据
- ✅ 获取看板股票 - 看板不存在
- ✅ 删除看板股票 - 正常删除
- ✅ 删除看板股票 - 股票不存在
- ✅ 删除看板股票 - 看板不存在
- ✅ 股票排序 - 正常排序
- ✅ 股票搜索 - 正常搜索
- ✅ 股票搜索 - 空关键词
- ✅ 股票搜索 - 无结果
- ✅ 股票搜索 - 单字符关键词

### 行情接口模块 (test_quotes.py)
- ✅ 获取单个股票行情 - 正常
- ✅ 获取单个股票行情 - 不存在的代码
- ✅ 获取多个股票行情 - 正常
- ✅ 获取多个股票行情 - 空代码列表
- ✅ 获取 K 线数据 - 正常
- ✅ 获取 K 线数据 - 周期参数验证
- ✅ 获取 K 线数据 - count 边界值
- ✅ 缓存机制 (Mock)

### 用户设置模块 (test_settings.py)
- ✅ 获取用户设置 - 首次获取 (自动创建默认)
- ✅ 获取用户设置 - 已存在
- ✅ 更新用户设置 - 正常更新全部字段
- ✅ 更新用户设置 - 只更新部分字段
- ✅ 更新用户设置 - refresh_interval 边界值
- ✅ 更新用户设置 - theme 验证
- ✅ 更新用户设置 - data_sources 验证

### 健康检查模块 (test_health.py)
- ✅ 根路径访问
- ✅ /health 端点
- ✅ /health/live 端点
- ✅ /health/ready 端点
- ✅ API 文档访问

### 边界情况和集成测试 (test_boundary_cases.py)
- ✅ 无认证访问所有需要认证的端点
- ✅ 使用他人 token 访问受限资源
- ✅ 超长输入测试
- ✅ 特殊字符输入测试
- ✅ 空输入/None 值测试
- ✅ 删除带有股票的看板
- ✅ 审计日志完整性检查
- ✅ 全局异常处理
- ✅ 完整用户工作流测试

## Fixtures 说明

### client
测试客户端，自动覆盖数据库依赖为内存 SQLite。

### test_db
测试数据库会话。

### test_user_data
测试用户数据字典: `{"username": "testuser", "password": "testpass123"}`

### test_user
已创建的测试用户对象，包含默认设置。

### auth_headers
包含认证 token 的请求头字典: `{"Authorization": "Bearer <token>"}`

### test_board
属于 test_user 的测试看板。

### test_stock
属于 test_board 的测试股票。

### test_user2 / auth_headers_user2
第二个测试用户和其认证头，用于权限测试。

## 已修复的 Bug

1. **datasources/__init__.py**: 缺少 `Optional` 导入
2. **cache.py**: `get_redis()` 函数类型注解不正确

## 测试策略

- 使用内存 SQLite 数据库进行测试，数据隔离
- 每个测试函数独立运行
- 使用 pytest-asyncio 支持异步测试
- Mock 数据源避免外部 API 调用
- 测试边界条件和错误处理
- 验证权限控制机制
