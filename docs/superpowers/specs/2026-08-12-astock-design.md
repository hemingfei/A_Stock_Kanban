# A股看盘工具设计文档

**日期**: 2026-08-12  
**版本**: 1.3  
**作者**: Claude  
**变更记录**:
- v1.0 (2026-08-12): 初始版本
- v1.1 (2026-08-12): 优化版本 - 新增安全设计、缓存架构、可观测性、Docker多容器编排
- v1.2 (2026-08-12): 深度优化 - 新增WebSocket协议、错误处理、数据模型、多环境配置、运维脚本
- v1.3 (2026-08-12): 生产级优化 - 新增数据库迁移、测试策略、CI/CD、性能优化、审计日志、状态管理

## 0. 本次优化摘要

| 优化项 | 说明 |
|--------|------|
| WebSocket协议 | 新增消息格式、心跳机制、订阅管理、重连策略 |
| 错误处理 | 新增统一错误响应格式、错误码定义 |
| 数据源容错 | 新增熔断器模式、降级策略、多数据源切换逻辑 |
| JWT刷新 | 新增Token刷新流程、Refresh Token设计 |
| 配置文件 | 新增nginx.conf、redis.conf、logging.conf完整示例 |
| 数据模型 | 新增行情、个股详情、K线数据的字段定义 |
| 限流实现 | 新增slowapi选型和实现思路 |
| 多环境配置 | 新增dev/staging/prod环境差异设计 |
| 运维脚本 | 新增数据库初始化、备份脚本设计 |
| 前端细节 | 新增错误边界、加载状态、TypeScript类型定义 |

## 1. 项目概述

### 1.1 项目目标
构建一个可部署到云服务器的A股看盘网页工具，支持多用户、自定义板块和个股配置，实时行情刷新。

### 1.2 核心功能
- 用户注册登录（账号密码）
- 自定义板块和板块内的个股
- 板块卡片网格布局，一屏看所有板块
- 实时行情刷新（可配置间隔，默认5秒）
- 涨跌幅排序
- 搜索/添加/删除个股
- K线图/分时图展示
- 个股详情页
- 多数据源配置
- 数据持久化（SQLite）

### 1.3 技术栈
- **后端**: FastAPI (Python)
- **前端**: React + TypeScript + Ant Design
- **图表**: Lightweight Charts
- **数据库**: SQLite
- **缓存**: Redis
- **部署**: Docker Compose + 腾讯云

---

## 2. 系统架构

### 2.0 项目根目录结构
```
astock/
├── .gitignore
├── .env.example
├── docker-compose.yml
├── README.md
├── backend/                 # 后端代码
├── frontend/                # 前端代码
├── nginx/                   # Nginx配置
│   ├── nginx.conf
│   └── ssl/                 # SSL证书目录
├── redis/                   # Redis配置
│   └── redis.conf
├── logs/                    # 日志目录（gitignore）
│   ├── nginx/
│   └── backend/
├── backup/                  # 备份目录（gitignore）
└── docs/                    # 文档
    └── superpowers/specs/
```

### 2.1 整体架构图
```
┌─────────────┐
│   浏览器    │
└──────┬──────┘
       │
       ├─ HTTPS → Nginx ──┬─→ React 静态文件
       │                   │
       └─ WebSocket        └─→ FastAPI API
                           
                       ┌───┴────┐
                       │ Redis  │ ← 缓存层
                       └───┬────┘
                           │
                       ┌───▼────┐
                       │ SQLite │
                       └────────┘
                       
数据层:
┌─────────────────────────────────────────┐
│  AkShare / Tushare / 其他数据源          │
└─────────────────────────────────────────┘
```

### 2.2 Docker部署架构
```
┌─────────────────────────────────────────────────────────────────┐
│                      Docker Compose                              │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │
│  │   Nginx容器     │  │  FastAPI容器    │  │   Redis容器     │  │
│  │  - 反向代理     │◄─►│  - 业务逻辑    │◄─►│  - 行情缓存    │  │
│  │  - 静态文件     │  │  - WebSocket   │  │  - Session存储 │  │
│  │  - HTTPS终止   │  │  - 数据源聚合   │  └─────────────────┘  │
│  └─────────────────┘  └────────┬────────┘                       │
│                                │                                │
│                         ┌──────▼──────┐                         │
│                         │  SQLite卷   │                         │
│                         │  数据持久化 │                         │
│                         └─────────────┘                         │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. 数据库设计

### 3.1 users 表（用户表）
```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### 3.2 boards 表（板块表）
```sql
CREATE TABLE boards (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    sort_order INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

### 3.3 stocks 表（个股表）
```sql
CREATE TABLE stocks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    board_id INTEGER NOT NULL,
    code TEXT NOT NULL,
    name TEXT NOT NULL,
    sort_order INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (board_id) REFERENCES boards(id)
);
```

### 3.4 user_settings 表（用户设置表）
```sql
CREATE TABLE user_settings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL UNIQUE,
    refresh_interval INTEGER DEFAULT 5,
    data_sources TEXT DEFAULT '["akshare"]',
    theme TEXT DEFAULT 'light',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

### 3.5 索引设计
```sql
-- 用户相关索引
CREATE INDEX idx_boards_user_id ON boards(user_id);
CREATE INDEX idx_user_settings_user_id ON user_settings(user_id);

-- 板块相关索引
CREATE INDEX idx_stocks_board_id ON stocks(board_id);

-- 个股查询索引
CREATE INDEX idx_stocks_code ON stocks(code);
```

### 3.6 数据备份策略
- **备份频率**: 每日凌晨2点自动备份
- **保留周期**: 保留最近7天的备份
- **备份方式**: SQLite `.dump` + 文件压缩
- **存储位置**: 宿主机挂载目录 `/backup`

---

## 4. API 设计

### 4.1 认证相关
| 方法 | 路径 | 描述 |
|------|------|------|
| POST | `/api/auth/register` | 用户注册 |
| POST | `/api/auth/login` | 用户登录 |
| POST | `/api/auth/logout` | 用户登出 |
| GET | `/api/auth/me` | 获取当前用户信息 |

### 4.2 板块管理
| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/api/boards` | 获取我的板块列表 |
| POST | `/api/boards` | 创建板块 |
| PUT | `/api/boards/:id` | 更新板块 |
| DELETE | `/api/boards/:id` | 删除板块 |
| PUT | `/api/boards/reorder` | 重排板块顺序 |

### 4.3 个股管理
| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/api/boards/:boardId/stocks` | 获取板块下的个股 |
| POST | `/api/boards/:boardId/stocks` | 添加个股到板块 |
| DELETE | `/api/boards/:boardId/stocks/:stockId` | 从板块删除个股 |
| PUT | `/api/boards/:boardId/stocks/reorder` | 重排个股顺序 |

### 4.4 搜索
| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/api/stocks/search` | 搜索个股 |

### 4.5 行情
| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/api/quotes` | 获取行情（批量） |
| GET | `/api/stocks/:code/kline` | 获取K线数据 |
| WS | `/ws/quotes` | 实时行情推送 |

### 4.6 设置
| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/api/settings` | 获取用户设置 |
| PUT | `/api/settings` | 更新用户设置 |

### 4.7 健康检查
| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/health` | 应用健康状态 |
| GET | `/health/live` | 存活检查 |
| GET | `/health/ready` | 就绪检查（含Redis、数据源） |

---

## 5. 前端设计

### 5.1 页面路由
| 路径 | 页面 | 描述 |
|------|------|------|
| `/login` | Login | 登录页 |
| `/register` | Register | 注册页 |
| `/` | Dashboard | 主看盘页（需登录） |
| `/stock/:code` | StockDetail | 个股详情页（需登录） |

### 5.2 主看盘页布局
```
┌─────────────────────────────────────────────────────────┐
│  Logo      [搜索框]      用户头像▼   [设置]              │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │  白酒板块   │  │  新能源板块 │  │  科技板块   │  │
│  ├──────────────┤  ├──────────────┤  ├──────────────┤  │
│  │ 名称  最新  │  │ 名称  最新  │  │ 名称  最新  │  │
│  │ 茅台 1800↑ │  │ 宁德 200↓  │  │ 中芯 50↑  │  │
│  │ 五粮 150↑  │  │ 比亚迪 250↑│  │ 寒武纪 200↑│  │
│  │ ...        │  │ ...         │  │ ...         │  │
│  │ [+添加个股] │  │ [+添加个股] │  │ [+添加个股] │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
│                                                         │
│  ┌──────────────┐                                       │
│  │ [+新建板块] │                                       │
│  └──────────────┘                                       │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### 5.3 个股详情页
```
┌─────────────────────────────────────────────────────────┐
│  ← 返回                          600519 贵州茅台      │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  最新价: 1800.00  +2.5%  +45.00                        │
│  今开: 1755.00  最高: 1810.00  成交量: 2.5万手        │
│  昨收: 1755.00  最低: 1750.00  成交额: 45亿           │
│                                                         │
│  ┌─────────────────────────────────────────────────┐  │
│  │              K线图 / 分时图  [切换]             │  │
│  │                                                 │  │
│  │   (Lightweight Charts 渲染)                     │  │
│  │                                                 │  │
│  └─────────────────────────────────────────────────┘  │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### 5.4 前端目录结构
```
frontend/
├── package.json
├── .env.example          # 环境变量模板
├── nginx.conf
├── Dockerfile
├── src/
│   ├── main.tsx
│   ├── App.tsx
│   ├── pages/
│   │   ├── Login.tsx
│   │   ├── Register.tsx
│   │   ├── Dashboard.tsx
│   │   └── StockDetail.tsx
│   ├── components/
│   │   ├── BoardCard.tsx
│   │   ├── StockList.tsx
│   │   ├── StockSearch.tsx
│   │   ├── KLineChart.tsx
│   │   └── SettingsModal.tsx
│   ├── hooks/
│   │   ├── useAuth.ts
│   │   ├── useBoards.ts
│   │   └── useQuotes.ts
│   ├── services/
│   │   ├── api.ts
│   │   └── ws.ts
│   ├── store/
│   │   └── index.ts       # Zustand store
│   ├── config.ts          # 配置管理
│   └── types/
│       └── index.ts
└── nginx.conf
```

---

## 6. 后端设计

### 6.1 数据源架构
```
datasources/
├── base.py          # 数据源基类
├── akshare.py       # AkShare实现
└── tushare.py       # Tushare实现
```

### 6.2 数据源策略
- **主数据源**: AkShare（免费、开源）
- **备用数据源**: Tushare（需要token）
- 支持配置数据源优先级和切换

### 6.2.1 熔断器模式

#### 熔断器状态机
```
closed（正常） → open（熔断） → half-open（半开）
     ↑                    ↓
     └────────────────────┘
```

#### 熔断参数
| 参数 | 值 | 说明 |
|------|-----|------|
| 失败阈值 | 5次 | 连续失败5次触发熔断 |
| 熔断时长 | 30秒 | 30秒内不调用数据源 |
| 半开尝试 | 1次 | 30秒后尝试1次请求 |
| 成功阈值 | 2次 | 半开状态连续成功2次恢复正常 |

#### 降级策略
- **熔断中**: 返回Redis中缓存的旧数据（如果有），标记为`stale: true`
- **无缓存**: 返回错误，前端显示「数据暂时不可用，使用上一次数据」
- **多数据源切换**: 主数据源熔断后，自动切换到备用数据源

### 6.2.2 多数据源切换逻辑
```typescript
async function getQuote(code: string): Promise<Quote> {
  const sources = getDataSourcePriority(); // [akshare, tushare]

  for (const source of sources) {
    if (isCircuitBreakerOpen(source)) {
      continue; // 跳过熔断中的数据源
    }

    try {
      const result = await source.getQuote(code);
      recordSuccess(source);
      return result;
    } catch (error) {
      recordFailure(source);
      logError(source, error);
      continue; // 尝试下一个数据源
    }
  }

  // 所有数据源都失败，尝试返回缓存数据
  const cached = await getCachedQuote(code);
  if (cached) {
    return { ...cached, stale: true };
  }

  throw new Error("所有数据源暂时不可用");
}
```

### 6.3 后端目录结构
```
backend/
├── main.py
├── requirements.txt
├── logging.conf          # 日志配置
├── app/
│   ├── __init__.py
│   ├── config.py         # 配置管理（环境变量）
│   ├── models.py         # SQLAlchemy models
│   ├── schemas.py        # Pydantic schemas
│   ├── auth.py           # 认证相关
│   ├── boards.py         # 板块API
│   ├── stocks.py         # 个股API
│   ├── quotes.py         # 行情API
│   ├── settings.py       # 设置API
│   ├── health.py         # 健康检查端点
│   ├── cache.py          # Redis缓存封装
│   ├── limiter.py        # 速率限制中间件
│   └── datasources/      # 数据源模块
│       ├── akshare.py
│       ├── tushare.py
│       └── base.py
├── data/
│   └── astock.db         # SQLite数据库
└── logs/                 # 日志目录
```

---

## 7. 数据流

### 7.1 实时行情更新流程
```
1. 用户登录 → 获取JWT token
2. 建立WebSocket连接
3. 前端发送订阅请求（用户的所有个股代码）
4. 后端先查Redis缓存，命中则直接返回
5. 缓存未命中则调用数据源获取数据
6. 数据回写Redis（设置5秒TTL）
7. 后端通过WebSocket推送更新
8. 前端更新界面
```

### 7.2 缓存查询流程
```
API请求 → 检查Redis缓存
              ├─ 命中 → 直接返回
              └─ 未命中 → 查询数据源
                              ├─ 成功 → 回写缓存 → 返回
                              └─ 失败 → 返回错误/降级数据
```

---

## 7.5 WebSocket协议设计

### 7.5.1 连接建立
- **连接URL**: `wss://your-domain.com/ws/quotes?token={jwt_token}`
- **握手阶段**: 通过query参数传递JWT进行认证
- **认证失败**: 立即关闭连接，返回401状态码

### 7.5.2 消息格式（JSON）

#### 客户端 → 服务端消息
```typescript
// 订阅行情
{
  "type": "subscribe",
  "data": {
    "codes": ["600519", "000001", "300750"]  // 股票代码列表
  }
}

// 取消订阅
{
  "type": "unsubscribe",
  "data": {
    "codes": ["600519"]
  }
}

// 心跳响应
{
  "type": "pong"
}
```

#### 服务端 → 客户端消息
```typescript
// 行情更新推送
{
  "type": "quote",
  "data": {
    "code": "600519",
    "price": 1800.00,
    "change": 45.00,
    "changePercent": 2.56
  }
}

// 批量行情更新
{
  "type": "quotes",
  "data": {
    "quotes": [
      { "code": "600519", "price": 1800.00, "change": 45.00, "changePercent": 2.56 },
      { "code": "000001", "price": 12.50, "change": -0.20, "changePercent": -1.57 }
    ]
  }
}

// 心跳ping
{
  "type": "ping"
}

// 错误消息
{
  "type": "error",
  "data": {
    "code": "ERROR_CODE",
    "message": "错误描述"
  }
}
```

### 7.5.3 心跳机制
- **心跳间隔**: 服务端每30秒发送ping
- **超时处理**: 客户端60秒未收到消息视为断开
- **心跳响应**: 客户端收到ping后回复pong
- **服务端超时**: 90秒未收到客户端消息则关闭连接

### 7.5.4 重连策略
```typescript
// 指数退避重连
const reconnectDelay = (attempt: number) => {
  const baseDelay = 1000;    // 1秒
  const maxDelay = 30000;    // 30秒
  const delay = Math.min(baseDelay * Math.pow(2, attempt), maxDelay);
  return delay; // 1s, 2s, 4s, 8s, 16s, 30s, 30s...
}
```

### 7.5.5 连接状态管理
```
disconnected → connecting → connected
                 ↓
            reconnecting ← (error/timeout)
```

状态事件：
- `connecting`: 开始连接
- `connected`: 连接成功
- `disconnected`: 连接断开
- `error`: 连接错误

---

## 7.8 错误处理设计

### 7.8.1 统一API错误响应格式
```typescript
// 错误响应
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",    // 错误码
    "message": "参数验证失败",     // 错误消息
    "details": [                   // 详细错误（可选）
      {
        "field": "username",
        "message": "用户名不能为空"
      }
    ],
    "requestId": "req_123abc"     // 请求ID，用于排查
  }
}

// 成功响应
{
  "success": true,
  "data": { ... }
}
```

### 7.8.2 错误码定义

| 错误码 | HTTP状态码 | 说明 |
|--------|-----------|------|
| `VALIDATION_ERROR` | 400 | 请求参数验证失败 |
| `AUTHENTICATION_ERROR` | 401 | 未认证/Token无效 |
| `AUTHORIZATION_ERROR` | 403 | 无权限访问 |
| `NOT_FOUND` | 404 | 资源不存在 |
| `RATE_LIMITED` | 429 | 请求过于频繁 |
| `INTERNAL_ERROR` | 500 | 服务器内部错误 |
| `DATASOURCE_ERROR` | 502 | 数据源错误 |
| `SERVICE_UNAVAILABLE` | 503 | 服务暂时不可用 |

### 7.8.3 异常处理流程
```
请求 → 中间件（限流、认证）
         ↓
      路由处理
         ↓
    业务逻辑
         ↓
  捕获异常 → 转换为统一错误格式 → 记录日志 → 返回响应
         ↓
    未捕获异常 → 500错误 → 记录详细堆栈 → 告警
```

---

## 8. 安全设计

### 8.1 认证与授权
- **JWT Token**: 无状态认证，Access Token有效期2小时，Refresh Token有效期7天
- **密码策略**: 最小长度8位，需包含字母和数字，bcrypt哈希存储（work factor=12）
- **CSRF防护**: 开启FastAPI CSRF保护，状态变更请求需验证token

### 8.1.1 JWT刷新流程

#### Token结构
```typescript
// Access Token（短期，用于API调用）
{
  "sub": "user_id",
  "type": "access",
  "exp": 1691827200  // 2小时后
}

// Refresh Token（长期，用于刷新Access Token）
{
  "sub": "user_id",
  "type": "refresh",
  "jti": "unique_token_id",  // 用于撤销
  "exp": 1692432000  // 7天后
}
```

#### 刷新流程
```
1. 前端检测Access Token即将过期（剩余<5分钟）
2. 前端调用 POST /api/auth/refresh，携带Refresh Token
3. 后端验证Refresh Token有效性
4. 后端返回新的Access Token（+可选的新Refresh Token）
5. 前端使用新Token继续请求
```

#### 刷新API
```typescript
// 请求
POST /api/auth/refresh
{
  "refreshToken": "eyJhbG..."
}

// 成功响应
{
  "success": true,
  "data": {
    "accessToken": "eyJhbG...",
    "tokenType": "Bearer",
    "expiresIn": 7200  // 2小时
  }
}
```

#### Token撤销
- 用户登出时将Refresh Token加入Redis黑名单
- 黑名单TTL = Refresh Token剩余有效期
- 刷新时检查黑名单

### 8.2 速率限制
| 接口 | 限制 | 说明 |
|------|------|------|
| 登录/注册 | 5次/分钟 | 防暴力破解 |
| 行情API | 60次/分钟 | 防数据源封禁 |
| 搜索API | 30次/分钟 | 防滥用 |

### 8.3 HTTPS
- 生产环境强制HTTPS，使用Let's Encrypt免费证书
- Nginx配置SSL证书，HTTP自动跳转HTTPS
- 设置安全头: HSTS、X-Content-Type-Options、X-Frame-Options

### 8.4 数据安全
- SQLite数据库文件权限限制为仅服务用户可读写
- 敏感配置（JWT secret、数据源token）通过环境变量传入
- 日志中不记录密码、token等敏感信息

---

## 9. 缓存架构设计

### 9.1 Redis缓存策略
| 缓存类型 | Key格式 | TTL | 说明 |
|----------|---------|-----|------|
| 个股行情 | `quote:{code}` | 5秒 | 与刷新间隔一致 |
| 批量行情 | `quotes:{hash(codes)}` | 5秒 | 批量查询缓存 |
| K线数据 | `kline:{code}:{period}` | 5分钟 | K线不频繁变化 |
| 搜索结果 | `search:{keyword}` | 1小时 | 股票列表相对稳定 |
| 个股信息 | `stock:{code}` | 24小时 | 基本信息很少变化 |

### 9.2 缓存更新策略
- **读穿透**: 先查缓存，未命中则查数据源，回写缓存
- **过期刷新**: TTL到期自动过期，下次请求刷新
- **主动更新**: WebSocket推送时同步更新缓存

### 9.3 Session存储
- JWT本身无状态，不依赖Session
- Redis可选存储活跃用户列表，用于在线统计

---

## 10. 可观测性设计

### 10.1 日志设计
- **结构化日志**: JSON格式，包含时间、级别、模块、消息、trace_id
- **日志级别**: DEBUG/INFO/WARNING/ERROR
- **日志轮转**: 按天轮转，保留30天
- **关键日志点**:
  - 用户登录/登出
  - 数据源调用成功/失败
  - API请求响应时间
  - 错误异常栈

### 10.2 健康检查
| 端点 | 说明 |
|------|------|
| `/health` | 应用健康状态 |
| `/health/ready` | 就绪检查（含Redis、数据源连通性） |
| `/health/live` | 存活检查 |

### 10.3 监控指标（后续扩展）
- API响应时间（P50/P95/P99）
- 错误率
- 缓存命中率
- 活跃WebSocket连接数

---

## 11. Docker部署方案

### 11.1 docker-compose.yml
```yaml
version: '3.8'

services:
  # Nginx 反向代理 + 静态文件服务
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/ssl:/etc/nginx/ssl:ro
      - frontend-build:/usr/share/nginx/html:ro
      - ./logs/nginx:/var/log/nginx
    depends_on:
      - backend
    restart: unless-stopped

  # FastAPI 后端服务
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    environment:
      - DATABASE_URL=sqlite:////app/data/astock.db
      - REDIS_URL=redis://redis:6379/0
      - JWT_SECRET_KEY=${JWT_SECRET_KEY:?Please set JWT_SECRET_KEY}
      - TUSHARE_TOKEN=${TUSHARE_TOKEN:-}
    volumes:
      - ./backend/data:/app/data
      - ./logs/backend:/app/logs
      - ./backup:/app/backup
    depends_on:
      - redis
    restart: unless-stopped

  # Redis 缓存
  redis:
    image: redis:7-alpine
    volumes:
      - redis-data:/data
      - ./redis/redis.conf:/usr/local/etc/redis/redis.conf:ro
    command: redis-server /usr/local/etc/redis/redis.conf
    restart: unless-stopped

  # 前端构建（仅构建阶段）
  frontend-builder:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    volumes:
      - frontend-build:/app/build

volumes:
  frontend-build:
  redis-data:
```

### 11.2 后端 Dockerfile
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 安装Python依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 创建必要目录
RUN mkdir -p /app/data /app/logs /app/backup

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health/live')"

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 11.3 前端 Dockerfile
```dockerfile
FROM node:18-alpine AS builder

WORKDIR /app

# 安装依赖
COPY package*.json ./
RUN npm ci

# 构建
COPY . .
RUN npm run build

# 仅输出构建产物（用于volume挂载）
FROM scratch
COPY --from=builder /app/build /build
```

### 11.4 环境变量配置 (.env.example)
```env
# JWT密钥（生产环境必须修改！）
JWT_SECRET_KEY=your-super-secret-key-here-change-in-production

# Tushare Token（可选）
TUSHARE_TOKEN=

# SQLite数据路径
DATABASE_URL=sqlite:////app/data/astock.db

# Redis连接
REDIS_URL=redis://redis:6379/0
```

### 11.5 .gitignore
```
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
ENV/
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Node
node_modules/
npm-debug.log*
yarn-debug.log*
yarn-error.log*
dist/
build/

# Database
*.db
*.sqlite
*.sqlite3

# Logs
*.log
logs/

# Environment
.env
.env.local

# IDE
.vscode/
.idea/
*.swp
*.swo

# Docker volumes
data/
backup/
redis-data/

# OS
.DS_Store
Thumbs.db
```

### 11.6 部署到腾讯云步骤
1. 购买腾讯云服务器（轻量应用服务器即可，推荐配置: 2核4G起）
2. 安装 Docker 和 Docker Compose
3. 上传代码到服务器
4. 复制 `.env.example` 为 `.env` 并配置敏感信息
5. 运行 `docker-compose up -d`
6. 配置域名解析（可选）
7. 配置SSL证书（使用certbot或云厂商证书）

---

## 12. 开发计划（分阶段）

### Phase 1: 基础框架
- 项目脚手架搭建（含 .gitignore、.env.example）
- 用户注册登录（含密码策略、JWT）
- 基础布局
- 日志系统

### Phase 2: 板块和个股管理
- 板块CRUD
- 个股添加/删除/排序
- 数据持久化（含索引）

### Phase 3: 行情数据
- 接入数据源
- 行情展示
- Redis缓存集成
- WebSocket实时推送

### Phase 4: 图表和详情
- K线图/分时图
- 个股详情页
- 涨跌幅排序

### Phase 5: 多数据源和设置
- 多数据源配置
- 用户设置页面
- 刷新间隔配置
- 速率限制

### Phase 6: 安全和可观测性
- HTTPS配置
- CSRF防护
- 健康检查端点
- 结构化日志

### Phase 7: 部署和优化
- Docker多容器编排
- 数据备份脚本
- 性能优化
- 错误处理

---

## 13. 技术选型理由

| 技术 | 理由 |
|------|------|
| FastAPI | 异步高性能，类型提示，自动API文档，适合WebSocket |
| React | 生态丰富，组件化开发 |
| Ant Design | 国内最流行，组件丰富，中文文档友好 |
| Lightweight Charts | TradingView出品，高性能K线图 |
| SQLite | 单文件数据库，部署简单，适合中小项目 |
| Redis | 高性能缓存，降低数据源请求频率，防限流 |
| Docker Compose | 多容器编排，服务隔离，易于扩展 |

---

## 14. 数据模型定义

### 14.1 行情数据字段
```typescript
interface Quote {
  code: string;           // 股票代码，如 "600519"
  name: string;           // 股票名称，如 "贵州茅台"
  market: "sh" | "sz";    // 市场：sh上交所，sz深交所

  // 价格数据
  price: number;          // 当前最新价
  preClose: number;       // 昨收价
  open: number;           // 今开价
  high: number;           // 最高价
  low: number;            // 最低价

  // 涨跌数据
  change: number;         // 涨跌额
  changePercent: number;  // 涨跌幅，如 2.56 表示 +2.56%

  // 成交数据
  volume: number;         // 成交量（手）
  amount: number;         // 成交额（万元）

  // 盘口数据
  bid1: number;           // 买一价
  bid1Volume: number;     // 买一量
  ask1: number;           // 卖一价
  ask1Volume: number;     // 卖一量

  // 元数据
  timestamp: number;      // 数据时间戳
  stale?: boolean;        // 是否为过期缓存数据
}
```

### 14.2 个股详情字段
```typescript
interface StockDetail {
  code: string;
  name: string;
  market: "sh" | "sz";

  // 基本信息
  listDate: string;       // 上市日期
  industry: string;       // 所属行业
  area: string;           // 地区

  // 股本数据
  totalShare: number;     // 总股本（万股）
  floatShare: number;     // 流通股本（万股）

  // 财务指标
  pe: number;             // 市盈率
  pb: number;             // 市净率
  eps: number;            // 每股收益
  bvps: number;           // 每股净资产

  // 行情数据（同Quote）
  quote: Quote;
}
```

### 14.3 K线数据字段
```typescript
interface KLineItem {
  date: string;           // 日期，如 "2024-01-01"
  open: number;           // 开盘价
  high: number;           // 最高价
  low: number;            // 最低价
  close: number;          // 收盘价
  volume: number;         // 成交量（手）
  amount: number;         // 成交额（万元）
  change: number;         // 涨跌额
  changePercent: number;  // 涨跌幅
}

// K线周期
type KLinePeriod = "1d" | "1w" | "1M" | "5m" | "15m" | "30m" | "60m";
```

---

## 15. 配置文件示例

### 15.1 nginx.conf
```nginx
user nginx;
worker_processes auto;
error_log /var/log/nginx/error.log warn;
pid /var/run/nginx.pid;

events {
    worker_connections 1024;
}

http {
    include       /etc/nginx/mime.types;
    default_type  application/octet-stream;

    log_format  main  '$remote_addr - $remote_user [$time_local] '
                      '"$request" $status $body_bytes_sent '
                      '"$http_referer" "$http_user_agent"';

    access_log  /var/log/nginx/access.log  main;

    sendfile        on;
    tcp_nopush      on;
    tcp_nodelay     on;
    keepalive_timeout  65;

    # 限流配置
    limit_req_zone $binary_remote_addr zone=api_limit:10m rate=60r/m;

    # Gzip压缩
    gzip on;
    gzip_types text/plain text/css application/json application/javascript;
    gzip_min_length 1000;

    # HTTP → HTTPS重定向
    server {
        listen 80;
        server_name your-domain.com;
        return 301 https://$server_name$request_uri;
    }

    # HTTPS服务
    server {
        listen 443 ssl http2;
        server_name your-domain.com;

        # SSL证书配置
        ssl_certificate /etc/nginx/ssl/fullchain.pem;
        ssl_certificate_key /etc/nginx/ssl/privkey.pem;
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_prefer_server_ciphers on;
        ssl_ciphers HIGH:!aNULL:!MD5;

        # 安全头
        add_header X-Frame-Options DENY always;
        add_header X-Content-Type-Options nosniff always;
        add_header X-XSS-Protection "1; mode=block" always;
        add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

        # 前端静态文件
        location / {
            root /usr/share/nginx/html;
            index index.html;
            try_files $uri $uri/ /index.html;

            # 静态文件缓存
            location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf)$ {
                expires 1y;
                add_header Cache-Control "public, immutable";
            }
        }

        # API代理
        location /api/ {
            limit_req zone=api_limit burst=10;
            proxy_pass http://backend:8000/api/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;

            # 超时配置
            proxy_connect_timeout 30s;
            proxy_send_timeout 30s;
            proxy_read_timeout 30s;
        }

        # WebSocket代理
        location /ws/ {
            proxy_pass http://backend:8000/ws/;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_read_timeout 300s;  # WebSocket长连接超时
        }

        # 健康检查端点
        location /health {
            proxy_pass http://backend:8000/health;
            access_log off;
        }
    }
}
```

### 15.2 redis.conf
```redis
# 网络配置
bind 0.0.0.0
port 6379

# 持久化配置
save 900 1      # 900秒内至少1次修改
save 300 10     # 300秒内至少10次修改
save 60 10000   # 60秒内至少10000次修改

# RDB文件名
dbfilename dump.rdb

# 数据目录
dir /data

# AOF持久化
appendonly yes
appendfsync everysec

# 内存策略（LRU）
maxmemory 256mb
maxmemory-policy allkeys-lru

# 慢查询日志
slowlog-log-slower-than 10000  # 10ms
slowlog-max-len 128

# 安全（生产环境应启用密码）
# requirepass your-redis-password
```

### 15.3 logging.conf
```ini
[loggers]
keys=root,uvicorn,sqlalchemy,datasource

[handlers]
keys=console,file

[formatters]
keys=json,standard

[logger_root]
level=INFO
handlers=console,file

[logger_uvicorn]
level=INFO
handlers=console,file
qualname=uvicorn
propagate=0

[logger_sqlalchemy]
level=WARNING
handlers=console,file
qualname=sqlalchemy.engine
propagate=0

[logger_datasource]
level=INFO
handlers=console,file
qualname=datasource
propagate=0

[handler_console]
class=StreamHandler
level=INFO
formatter=standard
args=(sys.stdout,)

[handler_file]
class=handlers.TimedRotatingFileHandler
level=INFO
formatter=json
args=("/app/logs/app.log", "midnight", 1, 30, "UTF-8")

[formatter_standard]
format=%(asctime)s - %(name)s - %(levelname)s - %(message)s
datefmt=%Y-%m-%d %H:%M:%S

[formatter_json]
class=app.logging.JsonFormatter
format=%(asctime)s %(name)s %(levelname)s %(message)s %(trace_id)s
```

---

## 16. 限流实现方案

### 16.1 技术选型
- **库**: `slowapi` + `limits`
- **存储**: Redis（分布式限流）
- **策略**: 滑动窗口

### 16.2 requirements.txt补充
```txt
fastapi>=0.100.0
uvicorn[standard]>=0.23.0
sqlalchemy>=2.0.0
aiosqlite>=0.19.0
redis>=5.0.0
python-jose[cryptography]>=3.3.0
passlib[bcrypt]>=1.7.4
python-multipart>=0.0.6
pydantic>=2.0.0
pydantic-settings>=2.0.0
# 限流相关
slowapi>=0.1.9
limits>=3.5.0
# 熔断相关
tenacity>=8.2.0
# 日志相关
python-json-logger>=2.0.7
```

### 16.3 限流中间件实现思路
```python
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request, status
from fastapi.responses import JSONResponse

limiter = Limiter(
    key_func=get_remote_address,
    storage_uri="redis://redis:6379/1"  # 使用独立的Redis库
)

# 注册异常处理器
@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={
            "success": False,
            "error": {
                "code": "RATE_LIMITED",
                "message": "请求过于频繁，请稍后再试",
                "requestId": str(request.state.request_id)
            }
        }
    )

# 使用示例
@app.get("/api/quotes")
@limiter.limit("60/minute")
async def get_quotes(request: Request, codes: str):
    ...
```

---

## 17. 多环境配置

### 17.1 环境差异

| 配置项 | 开发环境 | 测试环境 | 生产环境 |
|--------|---------|---------|---------|
| `DEBUG` | `true` | `false` | `false` |
| `LOG_LEVEL` | `DEBUG` | `INFO` | `INFO` |
| `DB_ECHO` | `true` | `false` | `false` |
| `CORS_ORIGINS` | `["*"]` | `["test-domain"]` | `["prod-domain"]` |
| `RATE_LIMIT_ENABLED` | `false` | `true` | `true` |
| `HTTPS_ONLY` | `false` | `true` | `true` |

### 17.2 .env文件示例

#### .env.development
```env
# 开发环境
ENV=development
DEBUG=true
LOG_LEVEL=DEBUG

# 数据库
DATABASE_URL=sqlite:///./data/astock_dev.db

# Redis
REDIS_URL=redis://localhost:6379/0

# JWT
JWT_SECRET_KEY=dev-secret-key-change-in-production
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_HOURS=24  # 开发环境Token有效期更长

# 数据源
TUSHARE_TOKEN=your-tushare-token

# 限流（开发环境关闭）
RATE_LIMIT_ENABLED=false

# CORS
CORS_ORIGINS=["http://localhost:3000","http://localhost:5173"]
```

#### .env.production
```env
# 生产环境
ENV=production
DEBUG=false
LOG_LEVEL=INFO

# 数据库
DATABASE_URL=sqlite:////app/data/astock.db

# Redis
REDIS_URL=redis://redis:6379/0

# JWT（必须通过环境变量设置强密钥）
JWT_SECRET_KEY=${JWT_SECRET_KEY:?JWT_SECRET_KEY is required}
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_HOURS=2
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# 数据源
TUSHARE_TOKEN=${TUSHARE_TOKEN:-}

# 限流
RATE_LIMIT_ENABLED=true

# CORS
CORS_ORIGINS=["https://your-domain.com"]

# HTTPS
HTTPS_ONLY=true
```

### 17.3 配置加载策略
```python
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    env: str = "development"
    debug: bool = False

    # 数据库
    database_url: str

    # Redis
    redis_url: str

    # JWT
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_hours: int = 2
    jwt_refresh_token_expire_days: int = 7

    # 限流
    rate_limit_enabled: bool = True

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

@lru_cache()
def get_settings() -> Settings:
    return Settings()
```

---

## 18. 运维脚本设计

### 18.1 项目结构补充
```
astock/
├── scripts/
│   ├── init_db.py          # 数据库初始化
│   ├── backup_db.sh        # 数据库备份
│   ├── restore_db.sh       # 数据库恢复
│   └── health_check.py     # 健康检查
├── ...
```

### 18.2 数据库初始化脚本 (scripts/init_db.py)
```python
"""
数据库初始化脚本
用法: python scripts/init_db.py [--reset]
"""
import asyncio
import argparse
from sqlalchemy import text
from app.database import engine, Base

async def init_database(reset: bool = False):
    async with engine.begin() as conn:
        if reset:
            print("⚠️  正在删除所有表...")
            await conn.run_sync(Base.metadata.drop_all)

        print("📊 正在创建表...")
        await conn.run_sync(Base.metadata.create_all)

        print("✅ 创建索引...")
        # 索引已在model中定义

        print("🎉 数据库初始化完成！")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="初始化数据库")
    parser.add_argument("--reset", action="store_true", help="重置数据库（删除所有数据）")
    args = parser.parse_args()

    asyncio.run(init_database(args.reset))
```

### 18.3 数据库备份脚本 (scripts/backup_db.sh)
```bash
#!/bin/bash
# 数据库备份脚本
# 用法: ./scripts/backup_db.sh

BACKUP_DIR="/app/backup"
DB_FILE="/app/data/astock.db"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/astock_${DATE}.db.gz"
KEEP_DAYS=7

mkdir -p "$BACKUP_DIR"

echo "📦 开始备份数据库: $DB_FILE"

# 使用SQLite的backup命令
sqlite3 "$DB_FILE" ".backup '${BACKUP_DIR}/temp_astock.db'"

# 压缩备份
gzip -c "${BACKUP_DIR}/temp_astock.db" > "$BACKUP_FILE"
rm "${BACKUP_DIR}/temp_astock.db"

echo "✅ 备份完成: $BACKUP_FILE"

# 删除7天前的备份
echo "🧹 删除${KEEP_DAYS}天前的备份..."
find "$BACKUP_DIR" -name "astock_*.db.gz" -mtime +$KEEP_DAYS -delete

echo "🎉 备份任务完成！"
```

### 18.4 定时备份配置 (docker-compose.yml补充)
```yaml
  # 后端服务补充
  backend:
    ...
    environment:
      ...
    # 添加cron任务
    command: >
      sh -c "
        echo '0 2 * * * /app/scripts/backup_db.sh' > /etc/crontabs/root &&
        crond -b &&
        uvicorn main:app --host 0.0.0.0 --port 8000
      "
```

### 18.5 健康检查脚本 (scripts/health_check.py)
```python
"""
健康检查脚本
用法: python scripts/health_check.py [--ready]
"""
import sys
import requests

BACKEND_URL = "http://localhost:8000"

def check_live():
    try:
        response = requests.get(f"{BACKEND_URL}/health/live", timeout=5)
        if response.status_code == 200:
            print("✅ 服务存活")
            return 0
        else:
            print(f"❌ 服务异常: {response.status_code}")
            return 1
    except Exception as e:
        print(f"❌ 检查失败: {e}")
        return 1

def check_ready():
    try:
        response = requests.get(f"{BACKEND_URL}/health/ready", timeout=5)
        if response.status_code == 200:
            print("✅ 服务就绪")
            return 0
        else:
            data = response.json()
            print(f"❌ 服务未就绪: {data.get('error', {}).get('message')}")
            return 1
    except Exception as e:
        print(f"❌ 检查失败: {e}")
        return 1

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="健康检查")
    parser.add_argument("--ready", action="store_true", help="检查就绪状态")
    args = parser.parse_args()

    if args.ready:
        sys.exit(check_ready())
    else:
        sys.exit(check_live())
```

---

## 19. 前端细节设计

### 19.1 TypeScript类型定义 (frontend/src/types/index.ts)
```typescript
// 用户相关
export interface User {
  id: string;
  username: string;
  createdAt: string;
}

export interface AuthState {
  user: User | null;
  accessToken: string | null;
  refreshToken: string | null;
  isAuthenticated: boolean;
}

// 板块相关
export interface Board {
  id: string;
  name: string;
  sortOrder: number;
  stocks: Stock[];
}

// 个股相关
export interface Stock {
  id: string;
  code: string;
  name: string;
  sortOrder: number;
}

// 行情相关
export interface Quote {
  code: string;
  name: string;
  market: "sh" | "sz";
  price: number;
  preClose: number;
  open: number;
  high: number;
  low: number;
  change: number;
  changePercent: number;
  volume: number;
  amount: number;
  bid1: number;
  bid1Volume: number;
  ask1: number;
  ask1Volume: number;
  timestamp: number;
  stale?: boolean;
}

// K线相关
export interface KLineItem {
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  amount: number;
  change: number;
  changePercent: number;
}

export type KLinePeriod = "1d" | "1w" | "1M" | "5m" | "15m" | "30m" | "60m";

// API响应相关
export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  error?: {
    code: string;
    message: string;
    details?: Array<{ field: string; message: string }>;
    requestId: string;
  };
}
```

### 19.2 错误边界设计 (frontend/src/components/ErrorBoundary.tsx)
```typescript
import React from 'react';

interface Props {
  children: React.ReactNode;
  fallback?: React.ReactNode;
}

interface State {
  hasError: boolean;
  error?: Error;
}

export class ErrorBoundary extends React.Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('ErrorBoundary caught an error:', error, errorInfo);
  }

  handleReset = () => {
    this.setState({ hasError: false, error: undefined });
  };

  render() {
    if (this.state.hasError) {
      return this.props.fallback || (
        <div className="flex flex-col items-center justify-center min-h-[400px] p-8">
          <div className="text-4xl mb-4">😵</div>
          <h2 className="text-xl font-bold mb-2">出了点问题</h2>
          <p className="text-gray-500 mb-4">别担心，我们已经记录了这个问题</p>
          <button
            onClick={this.handleReset}
            className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
          >
            重试
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}
```

### 19.3 加载状态组件 (frontend/src/components/Loading.tsx)
```typescript
import React from 'react';

interface LoadingProps {
  size?: 'sm' | 'md' | 'lg' | 'xl';
  text?: string;
  fullScreen?: boolean;
}

export const Loading: React.FC<LoadingProps> = ({
  size = 'md',
  text,
  fullScreen = false,
}) => {
  const sizeClasses = {
    sm: 'w-4 h-4',
    md: 'w-8 h-8',
    lg: 'w-12 h-12',
    xl: 'w-16 h-16',
  };

  const container = fullScreen ? (
    <div className="fixed inset-0 flex items-center justify-center bg-white/80 z-50">
      <div className="flex flex-col items-center">
        <Spinner className={sizeClasses[size]} />
        {text && <p className="mt-4 text-gray-600">{text}</p>}
      </div>
    </div>
  ) : (
    <div className="flex flex-col items-center justify-center p-8">
      <Spinner className={sizeClasses[size]} />
      {text && <p className="mt-4 text-gray-600">{text}</p>}
    </div>
  );

  return container;
};

const Spinner: React.FC<{ className?: string }> = ({ className }) => (
  <svg
    className={`animate-spin text-blue-500 ${className}`}
    viewBox="0 0 24 24"
    fill="none"
  >
    <circle
      className="opacity-25"
      cx="12"
      cy="12"
      r="10"
      stroke="currentColor"
      strokeWidth="4"
    />
    <path
      className="opacity-75"
      fill="currentColor"
      d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
    />
  </svg>
);

export const EmptyState: React.FC<{
  icon?: React.ReactNode;
  title: string;
  description?: string;
  action?: React.ReactNode;
}> = ({ icon, title, description, action }) => (
  <div className="flex flex-col items-center justify-center p-12 text-center">
    <div className="text-6xl mb-4 text-gray-300">{icon || '📭'}</div>
    <h3 className="text-lg font-medium text-gray-900 mb-2">{title}</h3>
    {description && <p className="text-gray-500 mb-4 max-w-sm">{description}</p>}
    {action}
  </div>
);
```

### 19.4 WebSocket Hook设计 (frontend/src/hooks/useWebSocket.ts)
```typescript
import { useEffect, useRef, useState, useCallback } from 'react';
import { getAccessToken } from '../services/auth';

type WebSocketStatus = 'disconnected' | 'connecting' | 'connected';

interface UseWebSocketOptions {
  onMessage?: (data: any) => void;
  onError?: (error: Event) => void;
  onOpen?: () => void;
  onClose?: () => void;
  reconnect?: boolean;
  maxReconnectAttempts?: number;
}

export function useWebSocket(options: UseWebSocketOptions = {}) {
  const {
    onMessage,
    onError,
    onOpen,
    onClose,
    reconnect = true,
    maxReconnectAttempts = 10,
  } = options;

  const wsRef = useRef<WebSocket | null>(null);
  const [status, setStatus] = useState<WebSocketStatus>('disconnected');
  const reconnectAttempts = useRef(0);
  const reconnectTimeout = useRef<NodeJS.Timeout>();

  const getReconnectDelay = (attempt: number) => {
    const baseDelay = 1000;
    const maxDelay = 30000;
    const delay = Math.min(baseDelay * Math.pow(2, attempt), maxDelay);
    return delay;
  };

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    const token = getAccessToken();
    if (!token) return;

    setStatus('connecting');

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/quotes?token=${token}`;

    try {
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        console.log('WebSocket connected');
        setStatus('connected');
        reconnectAttempts.current = 0;
        onOpen?.();
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.type === 'ping') {
            ws.send(JSON.stringify({ type: 'pong' }));
            return;
          }
          onMessage?.(data);
        } catch (e) {
          console.error('WebSocket message parse error:', e);
        }
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        onError?.(error);
      };

      ws.onclose = (event) => {
        console.log('WebSocket closed:', event.code, event.reason);
        setStatus('disconnected');
        onClose?.();

        if (reconnect && reconnectAttempts.current < maxReconnectAttempts) {
          const delay = getReconnectDelay(reconnectAttempts.current);
          console.log(`Reconnecting in ${delay}ms...`);
          reconnectAttempts.current += 1;

          reconnectTimeout.current = setTimeout(() => {
            connect();
          }, delay);
        }
      };
    } catch (e) {
      console.error('WebSocket connection error:', e);
      setStatus('disconnected');
    }
  }, [onMessage, onError, onOpen, onClose, reconnect, maxReconnectAttempts]);

  const disconnect = useCallback(() => {
    if (reconnectTimeout.current) {
      clearTimeout(reconnectTimeout.current);
    }
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    reconnectAttempts.current = 0;
    setStatus('disconnected');
  }, []);

  const send = useCallback((data: any) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(data));
    }
  }, []);

  useEffect(() => {
    return () => {
      disconnect();
    };
  }, [disconnect]);

  return {
    status,
    connect,
    disconnect,
    send,
  };
}
```

---

## 20. 数据库迁移方案

### 20.1 技术选型
- **迁移工具**: Alembic（SQLAlchemy官方迁移工具）
- **迁移策略**: 版本化迁移、支持升级/降级

### 20.2 项目结构补充
```
backend/
├── alembic/
│   ├── versions/          # 迁移版本文件
│   │   └── 20240812_initial_schema.py
│   ├── env.py            # 环境配置
│   ├── script.py.mako    # 迁移脚本模板
│   └── README
├── alembic.ini           # Alembic配置
└── ...
```

### 20.3 alembic.ini配置
```ini
[alembic]
script_location = alembic
file_template = %%(year)d%(month).2d%(day).2d_%(hour).2d%(minute).2d_%(slug)s
prepend_sys_path = .

[post_write_hooks]

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console
qualname =

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
```

### 20.4 初始迁移脚本示例
```python
"""initial_schema

Revision ID: 20240812_initial
Revises: 
Create Date: 2024-08-12 10:00:00

"""
from alembic import op
import sqlalchemy as sa

revision = '20240812_initial'
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    # 用户表
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('username', sa.String(length=50), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('username')
    )
    op.create_index('idx_users_username', 'users', ['username'])

    # 用户设置表
    op.create_table(
        'user_settings',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('refresh_interval', sa.Integer(), server_default='5', nullable=False),
        sa.Column('data_sources', sa.Text(), server_default='["akshare"]', nullable=False),
        sa.Column('theme', sa.String(length=20), server_default='light', nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id')
    )
    op.create_index('idx_user_settings_user_id', 'user_settings', ['user_id'])

    # 板块表
    op.create_table(
        'boards',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('sort_order', sa.Integer(), server_default='0', nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_boards_user_id', 'boards', ['user_id'])

    # 个股表
    op.create_table(
        'stocks',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('board_id', sa.Integer(), nullable=False),
        sa.Column('code', sa.String(length=10), nullable=False),
        sa.Column('name', sa.String(length=50), nullable=False),
        sa.Column('sort_order', sa.Integer(), server_default='0', nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['board_id'], ['boards.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_stocks_board_id', 'stocks', ['board_id'])
    op.create_index('idx_stocks_code', 'stocks', ['code'])

    # 审计日志表
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('action', sa.String(length=50), nullable=False),
        sa.Column('resource_type', sa.String(length=50), nullable=True),
        sa.Column('resource_id', sa.Integer(), nullable=True),
        sa.Column('ip_address', sa.String(length=50), nullable=True),
        sa.Column('user_agent', sa.String(length=255), nullable=True),
        sa.Column('extra_data', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_audit_logs_user_id', 'audit_logs', ['user_id'])
    op.create_index('idx_audit_logs_action', 'audit_logs', ['action'])
    op.create_index('idx_audit_logs_created_at', 'audit_logs', ['created_at'])

def downgrade() -> None:
    op.drop_index('idx_audit_logs_created_at', table_name='audit_logs')
    op.drop_index('idx_audit_logs_action', table_name='audit_logs')
    op.drop_index('idx_audit_logs_user_id', table_name='audit_logs')
    op.drop_table('audit_logs')

    op.drop_index('idx_stocks_code', table_name='stocks')
    op.drop_index('idx_stocks_board_id', table_name='stocks')
    op.drop_table('stocks')

    op.drop_index('idx_boards_user_id', table_name='boards')
    op.drop_table('boards')

    op.drop_index('idx_user_settings_user_id', table_name='user_settings')
    op.drop_table('user_settings')

    op.drop_index('idx_users_username', table_name='users')
    op.drop_table('users')
```

### 20.5 迁移命令
```bash
# 初始化Alembic
alembic init alembic

# 创建新迁移
alembic revision -m "add_new_column"

# 自动生成迁移（对比模型）
alembic revision --autogenerate -m "initial_schema"

# 升级到最新版本
alembic upgrade head

# 升级到指定版本
alembic upgrade <revision_id>

# 降级一个版本
alembic downgrade -1

# 降级到初始状态
alembic downgrade base

# 查看迁移历史
alembic history

# 查看当前版本
alembic current
```

### 20.6 Docker中的迁移执行
```yaml
# docker-compose.yml 补充
services:
  backend:
    # ...
    command: >
      sh -c "
        echo 'Running migrations...' &&
        alembic upgrade head &&
        echo 'Migrations completed!' &&
        echo 'Starting server...' &&
        uvicorn main:app --host 0.0.0.0 --port 8000
      "
```

---

## 21. 测试策略

### 21.1 测试金字塔
```
        /\
       /E2E\      # 端到端测试（少数关键流程）
      /------\
     /集成测试\   # API集成、数据库集成（适量）
    /----------\
   / 单元测试   \  # 单元测试、工具函数（最多）
  /______________\
```

### 21.2 测试技术选型
- **单元测试**: pytest
- **E2E测试**: Playwright
- **测试覆盖率**: pytest-cov
- **Mock**: unittest.mock / pytest-mock
- **前端测试**: Vitest + React Testing Library

### 21.3 项目测试结构
```
astock/
├── backend/
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── conftest.py             # pytest配置
│   │   ├── unit/                   # 单元测试
│   │   │   ├── test_auth.py
│   │   │   ├── test_datasources.py
│   │   │   └── test_utils.py
│   │   ├── integration/            # 集成测试
│   │   │   ├── test_api_auth.py
│   │   │   ├── test_api_boards.py
│   │   │   ├── test_api_quotes.py
│   │   │   └── test_websocket.py
│   │   └── fixtures/               # 测试夹具
│   │       ├── db.py
│   │       ├── users.py
│   │       └── mocks.py
├── frontend/
│   ├── tests/
│   │   ├── unit/
│   │   ├── components/
│   │   └── e2e/
└── scripts/
    └── run_tests.sh
```

### 21.4 pytest配置 (pytest.ini)
```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts =
    --strict-markers
    --tb=short
    --cov=app
    --cov-report=term-missing
    --cov-report=html
    --cov-fail-under=80
markers =
    slow: Marks tests as slow
    integration: Marks tests as integration
    e2e: Marks tests as e2e
asyncio_mode = auto
```

### 21.5 后端测试示例
```python
# tests/conftest.py
import pytest
import asyncio
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base, get_session
from app.main import app

@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
async def test_db():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    async with async_session() as session:
        yield session
    await engine.dispose()

@pytest.fixture
def client(test_db):
    def _get_test_db():
        try:
            yield test_db
        finally:
            pass
    app.dependency_overrides[get_session] = _get_test_db
    return TestClient(app)

# tests/unit/test_auth.py
from app.auth import verify_password, get_password_hash

def test_password_hashing():
    password = "testpassword123"
    hashed = get_password_hash(password)
    assert hashed != password
    assert verify_password(password, hashed) is True

def test_password_hashing_invalid():
    password = "testpassword123"
    wrong_password = "wrongpassword456"
    hashed = get_password_hash(password)
    assert verify_password(wrong_password, hashed) is False

# tests/integration/test_api_auth.py
def test_register_user(client):
    response = client.post(
        "/api/auth/register",
        json={"username": "testuser", "password": "testpassword123"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "access_token" in data["data"]

def test_login_user(client):
    # 先注册
    client.post(
        "/api/auth/register",
        json={"username": "testuser", "password": "testpassword123"}
    )
    # 再登录
    response = client.post(
        "/api/auth/login",
        data={"username": "testuser", "password": "testpassword123"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "access_token" in data["data"]
```

### 21.6 前端测试示例
```typescript
// frontend/tests/unit/utils.test.ts
import { formatPrice, formatChangePercent } from '@/utils/format'

describe('formatPrice', () => {
  it('formats price with two decimal places', () => {
    expect(formatPrice(1800)).toBe('1,800.00')
  })
  it('formats price correctly', () => {
    expect(formatPrice(1800.56)).toBe('1,800.56')
  })
})

// frontend/tests/components/BoardCard.test.tsx
import { render, screen, fireEvent } from '@testing-library/react'
import { BoardCard } from '@/components/BoardCard'

const mockBoard = {
  id: '1',
  name: '白酒',
  sortOrder: 0,
  stocks: [
    { id: '1', code: '600519', name: '贵州茅台', sortOrder: 0 }
  ]
}

describe('BoardCard', () => {
  it('renders board name', () => {
    render(<BoardCard board={mockBoard} />)
    expect(screen.getByText('白酒')).toBeInTheDocument()
  })
  it('renders stocks', () => {
    render(<BoardCard board={mockBoard} />)
    expect(screen.getByText('贵州茅台')).toBeInTheDocument()
  })
})
```

### 21.7 测试运行脚本
```bash
#!/bin/bash
# scripts/run_tests.sh

set -e

echo "🧪 Running backend tests..."
cd backend
pytest tests/unit -v
pytest tests/integration -v

echo "🧪 Running frontend tests..."
cd ../frontend
npm run test:unit

echo "✅ All tests passed!"
```

---

## 22. CI/CD流程设计

### 22.1 技术选型
- **平台**: GitHub Actions
- **镜像仓库**: Docker Hub / GitHub Container Registry
- **部署目标**: 腾讯云服务器
- **触发条件**:
  - PR: 运行测试
  - main分支: 运行测试 + 构建 + 部署

### 22.2 GitHub Actions工作流
```yaml
# .github/workflows/ci.yml
name: CI/CD Pipeline

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

jobs:
  test:
    name: Run Tests
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.11"]
        node-version: ["18"]

    steps:
    - name: Checkout code
      uses: actions/checkout@v4

    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v5
      with:
        python-version: ${{ matrix.python-version }}
        cache: 'pip'

    - name: Install backend dependencies
      run: |
        cd backend
        pip install -r requirements.txt
        pip install pytest pytest-cov pytest-asyncio httpx

    - name: Run backend tests
      run: |
        cd backend
        pytest tests/unit -v

    - name: Set up Node.js ${{ matrix.node-version }}
      uses: actions/setup-node@v4
      with:
        node-version: ${{ matrix.node-version }}
        cache: 'npm'
        cache-dependency-path: frontend/package-lock.json

    - name: Install frontend dependencies
      run: |
        cd frontend
        npm ci

    - name: Run frontend tests
      run: |
        cd frontend
        npm run test:unit -- --run

  build-and-deploy:
    name: Build and Deploy
    runs-on: ubuntu-latest
    needs: test
    if: github.ref == 'refs/heads/main'
    environment: production

    steps:
    - name: Checkout code
      uses: actions/checkout@v4

    - name: Set up Docker Buildx
      uses: docker/setup-buildx-action@v3

    - name: Log in to Container Registry
      uses: docker/login-action@v3
      with:
        registry: ${{ env.REGISTRY }}
        username: ${{ github.actor }}
        password: ${{ secrets.GITHUB_TOKEN }}

    - name: Extract metadata
      id: meta
      uses: docker/metadata-action@v5
      with:
        images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}

    - name: Build and push backend
      uses: docker/build-push-action@v5
      with:
        context: ./backend
        file: ./backend/Dockerfile
        push: true
        tags: ${{ steps.meta.outputs.tags }}-backend
        labels: ${{ steps.meta.outputs.labels }}
        cache-from: type=gha
        cache-to: type=gha,mode=max

    - name: Build and push frontend
      uses: docker/build-push-action@v5
      with:
        context: ./frontend
        file: ./frontend/Dockerfile
        push: true
        tags: ${{ steps.meta.outputs.tags }}-frontend
        labels: ${{ steps.meta.outputs.labels }}
        cache-from: type=gha
        cache-to: type=gha,mode=max

    - name: Deploy to server
      uses: appleboy/ssh-action@v1.0.3
      with:
        host: ${{ secrets.SERVER_HOST }}
        username: ${{ secrets.SERVER_USER }}
        key: ${{ secrets.SSH_PRIVATE_KEY }}
        script: |
          cd /opt/astock
          docker-compose pull
          docker-compose down
          docker-compose up -d
          docker image prune -af

  notify:
    name: Notify
    runs-on: ubuntu-latest
    needs: build-and-deploy
    if: always()
    steps:
    - name: Send notification
      run: |
        echo "Deployment ${{ needs.build-and-deploy.result }}"
```

### 22.3 环境变量和密钥
需要在GitHub仓库设置以下Secrets:
- `GITHUB_TOKEN`: 自动提供
- `SERVER_HOST`: 服务器IP/域名
- `SERVER_USER`: 服务器用户名
- `SSH_PRIVATE_KEY`: SSH私钥

---

## 23. 前端性能优化策略

### 23.1 虚拟列表（应对大量股票数据）
```typescript
// frontend/src/components/VirtualList.tsx
import { useVirtualizer } from '@tanstack/react-virtual'

interface VirtualListProps {
  items: any[]
  itemHeight?: number
  renderItem: (item: any, index: number) => React.ReactNode
}

export const VirtualList = ({
  items,
  itemHeight = 60,
  renderItem
}: VirtualListProps) => {
  const parentRef = useRef<HTMLDivElement>(null)

  const virtualizer = useVirtualizer({
    count: items.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => itemHeight,
    overscan: 5
  })

  return (
    <div ref={parentRef} style={{ height: '100%', overflow: 'auto' }}>
      <div style={{ height: virtualizer.getTotalSize(), position: 'relative' }}>
        {virtualizer.getVirtualItems().map((virtualItem) => (
          <div
            key={virtualItem.key}
            style={{
              position: 'absolute',
              top: 0,
              left: 0,
              width: '100%',
              height: virtualItem.size,
              transform: `translateY(${virtualItem.start}px)`
            }}
          >
            {renderItem(items[virtualItem.index], virtualItem.index)}
          </div>
        ))}
      </div>
    </div>
  )
}
```

### 23.2 防抖节流Hook
```typescript
// frontend/src/hooks/useDebounce.ts
import { useState, useEffect } from 'react'

export function useDebounce<T>(value: T, delay: number = 300): T {
  const [debouncedValue, setDebouncedValue] = useState<T>(value)

  useEffect(() => {
    const timer = setTimeout(() => setDebouncedValue(value), delay)
    return () => clearTimeout(timer)
  }, [value, delay])

  return debouncedValue
}

// frontend/src/hooks/useThrottle.ts
import { useRef, useCallback } from 'react'

export function useThrottle<T extends (...args: any[]) => any>(
  func: T,
  limit: number = 300
): T {
  const inThrottle = useRef(false)

  return useCallback(
    (...args: any[]) => {
      if (!inThrottle.current) {
        func(...args)
        inThrottle.current = true
        setTimeout(() => { inThrottle.current = false }, limit)
      }
    },
    [func, limit]
  ) as T
}
```

### 23.3 代码分割策略
```typescript
// frontend/src/router/index.tsx
import { lazy, Suspense } from 'react'
import { createBrowserRouter } from 'react-router-dom'
import { Loading } from '@/components/Loading'

// 懒加载页面
const Dashboard = lazy(() => import('@/pages/Dashboard'))
const StockDetail = lazy(() => import('@/pages/StockDetail'))
const Login = lazy(() => import('@/pages/Login'))
const Register = lazy(() => import('@/pages/Register'))

// Suspense包装
const PageLoader = () => <Loading text="加载中..." />

export const router = createBrowserRouter([
  {
    path: '/',
    element: (
      <Suspense fallback={<PageLoader />}>
        <RequireAuth>
          <Dashboard />
        </RequireAuth>
      </Suspense>
    )
  },
  {
    path: '/stock/:code',
    element: (
      <Suspense fallback={<PageLoader />}>
        <RequireAuth>
          <StockDetail />
        </RequireAuth>
      </Suspense>
    )
  },
  {
    path: '/login',
    element: (
      <Suspense fallback={<PageLoader />}>
        <Login />
      </Suspense>
    )
  },
  {
    path: '/register',
    element: (
      <Suspense fallback={<PageLoader />}>
        <Register />
      </Suspense>
    )
  }
])
```

### 23.4 前端缓存策略
```typescript
// frontend/src/hooks/useSWR.ts
import useSWR from 'swr'
import { api } from '@/services/api'

const fetcher = (url: string) => api.get(url).then(res => res.data)

export function useBoards() {
  return useSWR('/api/boards', fetcher, {
    refreshInterval: 30000, // 30秒刷新
    revalidateOnFocus: true,
    errorRetryCount: 3
  })
}

export function useStockDetail(code: string) {
  return useSWR(code ? `/api/stocks/${code}` : null, fetcher, {
    revalidateIfStale: false,
    dedupingInterval: 60000 // 1分钟
  })
}

export function useKLineData(code: string, period: KLinePeriod) {
  return useSWR(
    code ? `/api/stocks/${code}/kline?period=${period}` : null,
    fetcher,
    {
      revalidateIfStale: false,
      dedupingInterval: 300000 // 5分钟
    }
  )
}
```

### 23.5 性能监控
```typescript
// frontend/src/utils/performance.ts
// 记录性能指标
export const reportWebVitals = (onPerfEntry?: (metric: any) => void) => {
  if (onPerfEntry && onPerfEntry instanceof Function) {
    import('web-vitals').then(({ getCLS, getFID, getFCP, getLCP, getTTFB }) => {
      getCLS(onPerfEntry)
      getFID(onPerfEntry)
      getFCP(onPerfEntry)
      getLCP(onPerfEntry)
      getTTFB(onPerfEntry)
    })
  }
}

// 自定义性能指标
export const Performance = {
  start(name: string) {
    performance.mark(`${name}-start`)
  },
  end(name: string) {
    performance.mark(`${name}-end`)
    performance.measure(name, `${name}-start`, `${name}-end`)
    const measure = performance.getEntriesByName(name)[0]
    console.debug(`[Performance] ${name}: ${measure.duration.toFixed(2)}ms`)
    return measure.duration
  }
}
```

---

## 24. 用户操作审计日志

### 24.1 审计日志数据模型
```python
# backend/app/models.py
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .database import Base

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    action = Column(String(50), nullable=False, index=True)  # login, create, update, delete
    resource_type = Column(String(50), nullable=True)  # board, stock, user_setting
    resource_id = Column(Integer, nullable=True)
    ip_address = Column(String(50), nullable=True)
    user_agent = Column(String(255), nullable=True)
    extra_data = Column(Text, nullable=True)  # JSON格式的额外数据
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    user = relationship("User")
```

### 24.2 审计日志操作类型
| 操作类型 | 说明 |
|---------|------|
| user_register | 用户注册 |
| user_login | 用户登录 |
| user_logout | 用户登out |
| board_create | 创建板块 |
| board_update | 更新板块 |
| board_delete | 删除板块 |
| stock_add | 添加个股 |
| stock_remove | 删除个股 |
| settings_update | 更新设置 |
| kline_view | 查看K线图 |

### 24.3 审计日志中间件
```python
# backend/app/audit.py
import json
from functools import wraps
from typing import Optional
from fastapi import Request, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from .database import get_session
from .models import AuditLog
from .auth import get_current_user

def audit_log(action: str, resource_type: Optional[str] = None):
    """审计日志装饰器"""
    def decorator(func):
        @wraps(func)
        async def wrapper(
            *args,
            request: Request = None,
            current_user = Depends(get_current_user),
            db: AsyncSession = Depends(get_session),
            **kwargs
        ):
            # 获取资源ID（从路径参数或响应中）
            resource_id = kwargs.get('id') or kwargs.get('board_id') or kwargs.get('stock_id')

            # 记录审计日志
            try:
                audit_log = AuditLog(
                    user_id=current_user.id if current_user else None,
                    action=action,
                    resource_type=resource_type,
                    resource_id=resource_id,
                    ip_address=get_client_ip(request),
                    user_agent=request.headers.get('user-agent'),
                    extra_data=json.dumps({'path': request.url.path}, ensure_ascii=False)
                )
                db.add(audit_log)
                await db.commit()
            except Exception:
                # 审计日志不影响主流程
                pass

            return await func(*args, request=request, current_user=current_user, db=db, **kwargs)
        return wrapper
    return decorator

def get_client_ip(request: Request) -> Optional[str]:
    """获取客户端IP"""
    x_forwarded_for = request.headers.get('X-Forwarded-For')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.client.host if request.client else None
```

### 24.4 审计日志API
```python
# backend/app/audit_api.py
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from datetime import datetime, timedelta
from .database import get_session
from .models import AuditLog, User
from .schemas import AuditLogSchema
from .auth import get_current_user, require_admin

router = APIRouter(prefix="/api/audit", tags=["audit"])

@router.get("/logs", response_model=list[AuditLogSchema])
async def get_audit_logs(
    user_id: Optional[int] = Query(None, description="过滤用户"),
    action: Optional[str] = Query(None, description="过滤操作"),
    start_date: Optional[datetime] = Query(None, description="开始日期"),
    end_date: Optional[datetime] = Query(None, description="结束日期"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_session)
):
    """获取审计日志（管理员）"""
    query = select(AuditLog)

    if user_id:
        query = query.where(AuditLog.user_id == user_id)
    if action:
        query = query.where(AuditLog.action == action)
    if start_date:
        query = query.where(AuditLog.created_at >= start_date)
    if end_date:
        query = query.where(AuditLog.created_at <= end_date)

    query = query.order_by(desc(AuditLog.created_at)).limit(limit).offset(offset)
    result = await db.execute(query)
    return result.scalars().all()

@router.get("/my-logs", response_model=list[AuditLogSchema])
async def get_my_audit_logs(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session)
):
    """获取当前用户的审计日志"""
    query = select(AuditLog).where(
        AuditLog.user_id == current_user.id
    ).order_by(desc(AuditLog.created_at)).limit(limit).offset(offset)
    result = await db.execute(query)
    return result.scalars().all()
```

### 24.5 审计日志清理策略
```python
# backend/scripts/clean_audit_logs.py
"""
清理超过保留期的审计日志
保留期：默认90天
用法: python scripts/clean_audit_logs.py --days 90
"""
import asyncio
import argparse
from datetime import datetime, timedelta
from sqlalchemy import delete
from app.database import async_session
from app.models import AuditLog

async def clean_old_logs(days: int = 90):
    cutoff_date = datetime.utcnow() - timedelta(days=days)

    async with async_session() as session:
        stmt = delete(AuditLog).where(AuditLog.created_at < cutoff_date)
        result = await session.execute(stmt)
        await session.commit()
        deleted_count = result.rowcount
        print(f"🧹 Deleted {deleted_count} audit logs older than {days} days")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Clean up old audit logs")
    parser.add_argument("--days", type=int, default=90, help="Retention period in days")
    args = parser.parse_args()
    asyncio.run(clean_old_logs(args.days))
```

---

## 25. API版本管理

### 25.1 版本策略
- **URI版本控制**: `/api/v1/boards`
- **版本格式**: v1, v2, v3...
- **向后兼容**: 小版本变更保持兼容
- **弃用策略**: 保留旧版本至少6个月

### 25.2 FastAPI版本控制实现
```python
# backend/app/api_v1.py
from fastapi import APIRouter
from . import boards, stocks, quotes, auth, settings

router = APIRouter(prefix="/api/v1")
router.include_router(auth.router)
router.include_router(boards.router)
router.include_router(stocks.router)
router.include_router(quotes.router)
router.include_router(settings.router)

# backend/app/api_v2.py (未来)
from fastapi import APIRouter
from .v2 import boards, stocks, quotes, auth, settings

router = APIRouter(prefix="/api/v2")
router.include_router(auth.router)
router.include_router(boards.router)
router.include_router(stocks.router)
router.include_router(quotes.router)
router.include_router(settings.router)

# backend/main.py
from fastapi import FastAPI
from app.api_v1 import router as api_v1_router
# from app.api_v2 import router as api_v2_router

app = FastAPI(title="A股看盘工具", version="1.0.0")
app.include_router(api_v1_router)
# app.include_router(api_v2_router)

# 重定向旧版API（如果从 /api 变更到 /api/v1）
@app.get("/api/{path:path}")
async def redirect_to_v1(path: str):
    raise HTTPException(
        status_code=301,
        detail=f"API moved to /api/v1/{path}. Please update your client."
    )
```

### 25.3 版本响应头
```python
@app.middleware("http")
async def add_version_header(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-API-Version"] = "v1"
    return response
```

---

## 26. 前端状态管理（Zustand）

### 26.1 状态结构设计
```typescript
// frontend/src/store/index.ts
import { create } from 'zustand'
import { persist, createJSONStorage } from 'zustand/middleware'
import { User, Board, Quote } from '@/types'

interface AuthState {
  user: User | null
  accessToken: string | null
  refreshToken: string | null
  isAuthenticated: boolean
  setUser: (user: User | null) => void
  setTokens: (access: string, refresh: string) => void
  clearAuth: () => void
}

interface QuoteState {
  quotes: Map<string, Quote>
  updateQuote: (quote: Quote) => void
  updateQuotes: (quotes: Quote[]) => void
  getQuote: (code: string) => Quote | undefined
  clearQuotes: () => void
}

interface BoardState {
  boards: Board[]
  isLoading: boolean
  setBoards: (boards: Board[]) => void
  addBoard: (board: Board) => void
  updateBoard: (id: string, data: Partial<Board>) => void
  deleteBoard: (id: string) => void
  addStockToBoard: (boardId: string, stock: Stock) => void
  removeStockFromBoard: (boardId: string, stockId: string) => void
  reorderBoards: (boardIds: string[]) => void
}

interface UIState {
  theme: 'light' | 'dark'
  sidebarOpen: boolean
  refreshInterval: number
  setTheme: (theme: 'light' | 'dark') => void
  toggleSidebar: () => void
  setRefreshInterval: (interval: number) => void
}

// 认证状态（持久化）
export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      accessToken: null,
      refreshToken: null,
      isAuthenticated: false,
      setUser: (user) => set({ user }),
      setTokens: (accessToken, refreshToken) => set({
        accessToken,
        refreshToken,
        isAuthenticated: !!accessToken
      }),
      clearAuth: () => set({
        user: null,
        accessToken: null,
        refreshToken: null,
        isAuthenticated: false
      })
    }),
    {
      name: 'astock-auth',
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({
        accessToken: state.accessToken,
        refreshToken: state.refreshToken
      })
    }
  )
)

// 行情状态（不持久化）
export const useQuoteStore = create<QuoteState>((set, get) => ({
  quotes: new Map(),
  updateQuote: (quote) => set((state) => {
    const newQuotes = new Map(state.quotes)
    newQuotes.set(quote.code, quote)
    return { quotes: newQuotes }
  }),
  updateQuotes: (quotes) => set((state) => {
    const newQuotes = new Map(state.quotes)
    quotes.forEach(q => newQuotes.set(q.code, q))
    return { quotes: newQuotes }
  }),
  getQuote: (code) => get().quotes.get(code),
  clearQuotes: () => set({ quotes: new Map() })
}))

// 板块状态
export const useBoardStore = create<BoardState>((set) => ({
  boards: [],
  isLoading: false,
  setBoards: (boards) => set({ boards, isLoading: false }),
  addBoard: (board) => set((state) => ({
    boards: [...state.boards, board]
  })),
  updateBoard: (id, data) => set((state) => ({
    boards: state.boards.map(b =>
      b.id === id ? { ...b, ...data } : b
    )
  })),
  deleteBoard: (id) => set((state) => ({
    boards: state.boards.filter(b => b.id !== id)
  })),
  addStockToBoard: (boardId, stock) => set((state) => ({
    boards: state.boards.map(b =>
      b.id === boardId
        ? { ...b, stocks: [...b.stocks, stock] }
        : b
    )
  })),
  removeStockFromBoard: (boardId, stockId) => set((state) => ({
    boards: state.boards.map(b =>
      b.id === boardId
        ? { ...b, stocks: b.stocks.filter(s => s.id !== stockId) }
        : b
    )
  })),
  reorderBoards: (boardIds) => set((state) => ({
    boards: boardIds.map(id => state.boards.find(b => b.id === id)).filter(Boolean) as Board[]
  }))
}))

// UI状态（持久化）
export const useUIStore = create<UIState>()(
  persist(
    (set) => ({
      theme: 'light',
      sidebarOpen: true,
      refreshInterval: 5,
      setTheme: (theme) => set({ theme }),
      toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),
      setRefreshInterval: (interval) => set({ refreshInterval: interval })
    }),
    {
      name: 'astock-ui',
      storage: createJSONStorage(() => localStorage)
    }
  )
)

// 选择器辅助函数
export const useAllStockCodes = () => {
  return useBoardStore((state) =>
    state.boards.flatMap(b => b.stocks.map(s => s.code))
  )
}

export const useBoardQuotes = (boardId: string) => {
  const board = useBoardStore((state) =>
    state.boards.find(b => b.id === boardId)
  )
  const getQuote = useQuoteStore((state) => state.getQuote)
  return board?.stocks.map(stock => getQuote(stock.code)).filter(Boolean) as Quote[]
}
```

---

## 27. 监控告警机制

### 27.1 健康检查增强
```python
# backend/app/health.py
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from redis import asyncio as aioredis
from pydantic import BaseModel
from datetime import datetime
from .database import get_session
from .config import settings

router = APIRouter(prefix="/health", tags=["health"])

class HealthStatus(BaseModel):
    status: str
    database: str
    redis: str
    datasource: str
    timestamp: str
    uptime: float

# 记录启动时间
start_time = datetime.utcnow()

@router.get("")
async def get_health_status():
    """总体健康状态"""
    uptime = (datetime.utcnow() - start_time).total_seconds()
    return HealthStatus(
        status="healthy",
        database="ok",
        redis="ok",
        datasource="ok",
        timestamp=datetime.utcnow().isoformat(),
        uptime=uptime
    )

@router.get("/ready")
async def get_readiness(db: AsyncSession = Depends(get_session)):
    """就绪状态（包含数据库和Redis检查）"""
    checks = {
        "database": "unknown",
        "redis": "unknown"
    }

    # 检查数据库
    try:
        await db.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception:
        checks["database"] = "error"

    # 检查Redis
    try:
        redis = aioredis.from_url(settings.redis_url)
        await redis.ping()
        await redis.close()
        checks["redis"] = "ok"
    except Exception:
        checks["redis"] = "error"

    all_ok = all(v == "ok" for v in checks.values())

    return {
        "status": "ready" if all_ok else "not_ready",
        "checks": checks,
        "timestamp": datetime.utcnow().isoformat()
    }

@router.get("/live")
async def get_liveness():
    """存活状态"""
    return {"status": "alive", "timestamp": datetime.utcnow().isoformat()}
```

### 27.2 指标收集
```python
# backend/app/metrics.py
from prometheus_fastapi_instrumentator import Instrumentator, metrics
from fastapi import FastAPI

def setup_metrics(app: FastAPI):
    """设置Prometheus指标"""
    instrumentator = Instrumentator()

    # 添加默认指标
    instrumentator.add(metrics.request_count())
    instrumentator.add(metrics.request_duration())
    instrumentator.add(metrics.request_size())
    instrumentator.add(metrics.response_size())

    instrumentator.instrument(app).expose(app, include_in_schema=False)
```

### 27.3 告警策略
| 指标 | 阈值 | 严重程度 | 通知方式 |
|------|------|---------|---------|
| HTTP 5xx错误率 | >5% | 高 | 邮件/微信 |
| 响应时间P95 | >2秒 | 中 | 邮件 |
| 数据源失败率 | >10% | 高 | 邮件 |
| 活跃WebSocket连接 | 0持续5分钟 | 中 | 邮件 |
| Redis连接失败 | >5次 | 高 | 邮件 |
| 磁盘使用率 | >80% | 中 | 邮件 |

### 27.4 告警通知示例
```python
# backend/app/alert.py
import httpx
import logging
from typing import Optional
from .config import settings

logger = logging.getLogger(__name__)

class AlertManager:
    def __init__(self):
        self.webhook_url = settings.alert_webhook_url

    async def send_alert(
        self,
        title: str,
        message: str,
        severity: str = "warning"
    ):
        """发送告警通知"""
        if not self.webhook_url:
            logger.warning(f"[Alert] {title}: {message} (no webhook configured)")
            return

        try:
            async with httpx.AsyncClient() as client:
                await client.post(
                    self.webhook_url,
                    json={
                        "title": title,
                        "message": message,
                        "severity": severity,
                        "timestamp": datetime.utcnow().isoformat()
                    },
                    timeout=5.0
                )
            logger.info(f"[Alert] Sent: {title}")
        except Exception as e:
            logger.error(f"[Alert] Failed to send: {e}")

alert_manager = AlertManager()
```

---

## 28. 完整项目目录结构

```
astock/
├── .github/
│   └── workflows/
│       └── ci.yml                    # CI/CD工作流
├── .env.example                      # 环境变量示例
├── .gitignore
├── docker-compose.yml
├── README.md
├── docs/
│   └── superpowers/
│       └── specs/
│           └── 2024-08-12-astock-design.md
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── alembic.ini
│   ├── logging.conf
│   ├── main.py
│   ├── app/
│   │   ├── __init__.py
│   │   ├── config.py
│   │   ├── models.py
│   │   ├── schemas.py
│   │   ├── database.py
│   │   ├── auth.py
│   │   ├── audit.py
│   │   ├── cache.py
│   │   ├── limiter.py
│   │   ├── health.py
│   │   ├── metrics.py
│   │   ├── alert.py
│   │   ├── boards.py
│   │   ├── stocks.py
│   │   ├── quotes.py
│   │   ├── settings.py
│   │   └── datasources/
│   │       ├── __init__.py
│   │       ├── base.py
│   │       ├── akshare.py
│   │       └── tushare.py
│   ├── alembic/
│   │   ├── versions/
│   │   ├── env.py
│   │   └── script.py.mako
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── conftest.py
│   │   ├── unit/
│   │   └── integration/
│   ├── scripts/
│   │   ├── init_db.py
│   │   ├── backup_db.sh
│   │   ├── health_check.py
│   │   └── clean_audit_logs.py
│   ├── data/
│   │   └── (SQLite数据库文件)
│   └── logs/
│       └── (日志文件)
├── frontend/
│   ├── Dockerfile
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   ├── .env.example
│   ├── index.html
│   ├── nginx.conf
│   ├── public/
│   │   └── favicon.ico
│   ├── src/
│   │   ├── main.tsx
│   │   ├── App.tsx
│   │   ├── index.css
│   │   ├── router/
│   │   │   └── index.tsx
│   │   ├── pages/
│   │   │   ├── Login.tsx
│   │   │   ├── Register.tsx
│   │   │   ├── Dashboard.tsx
│   │   │   └── StockDetail.tsx
│   │   ├── components/
│   │   │   ├── Layout/
│   │   │   │   ├── Header.tsx
│   │   │   │   └── Sidebar.tsx
│   │   │   ├── BoardCard.tsx
│   │   │   ├── StockList.tsx
│   │   │   ├── StockSearch.tsx
│   │   │   ├── KLineChart.tsx
│   │   │   ├── QuoteRow.tsx
│   │   │   ├── SettingsModal.tsx
│   │   │   ├── Loading.tsx
│   │   │   ├── EmptyState.tsx
│   │   │   └── ErrorBoundary.tsx
│   │   ├── hooks/
│   │   │   ├── useAuth.ts
│   │   │   ├── useBoards.ts
│   │   │   ├── useQuotes.ts
│   │   │   ├── useWebSocket.ts
│   │   │   ├── useDebounce.ts
│   │   │   └── useThrottle.ts
│   │   ├── services/
│   │   │   ├── api.ts
│   │   │   ├── ws.ts
│   │   │   └── auth.ts
│   │   ├── store/
│   │   │   └── index.ts
│   │   ├── types/
│   │   │   └── index.ts
│   │   ├── utils/
│   │   │   ├── format.ts
│   │   │   ├── colors.ts
│   │   │   └── performance.ts
│   │   └── constants/
│   │       └── index.ts
│   └── tests/
│       ├── unit/
│       └── components/
├── nginx/
│   ├── nginx.conf
│   └── ssl/
│       ├── (证书文件)
├── redis/
│   └── redis.conf
└── scripts/
    ├── run_tests.sh
    └── deploy.sh
```

---

## 29. 后续可扩展功能
- 自选股提醒（价格涨跌幅告警）
- 技术指标（MA、MACD、KDJ等）
- 财报数据展示
- 新闻资讯
- 移动端适配优化
- 暗色主题
- 数据导出
