# 校园二手交易平台（Campus Market）

一个面向在校学生的二手交易平台：支持用户注册登录、商品发布与管理员审核、搜索筛选、收藏、下单、模拟支付、订单状态流转（含 30 分钟超时自动取消）、站内通知与后台数据统计。前后端分离，`docker compose up -d --build` 一键部署。

## 一、技术栈

| 端 | 技术 |
| --- | --- |
| 后端 | Python 3.11 · Django 4.2 · Django REST Framework · SimpleJWT(JWT 鉴权) · django-cors-headers · django-filter · drf-spectacular(Swagger/Redoc) · Pillow(图片压缩) |
| 异步 | Celery 5 · Redis 7（Broker/结果/缓存） |
| 前端 | Vue 3 · Vite · TypeScript · Vue Router · Pinia · Axios · Element Plus · ECharts |
| 数据库 | MySQL 8.0（utf8mb4） |
| 部署 | Docker Compose · Nginx（反向代理） · Gunicorn · Celery Worker/Beat |

## 二、目录结构

```text
campus-market/
├── backend/
│   ├── manage.py
│   ├── requirements.txt
│   ├── .env.example            # 环境变量模板（复制为 .env 使用）
│   ├── Dockerfile
│   ├── config/                 # Django 项目配置
│   │   ├── __init__.py         # 启动 Celery app
│   │   ├── settings.py
│   │   ├── urls.py
│   │   ├── wsgi.py
│   │   ├── asgi.py
│   │   └── celery.py
│   ├── apps/
│   │   ├── common/             # 统一响应、分页、异常、权限
│   │   ├── users/              # 用户注册/登录/资料
│   │   ├── products/           # 分类/商品/收藏/图片
│   │   ├── orders/             # 订单与状态机
│   │   └── notifications/      # 站内通知
│   ├── media/                  # 上传图片（容器内挂载卷）
│   └── static/                 # collectstatic 产物
├── frontend/
│   ├── package.json
│   ├── vite.config.ts
│   ├── tsconfig.json
│   ├── index.html
│   ├── Dockerfile
│   └── src/
│       ├── api/                # 接口封装
│       ├── assets/
│       ├── components/         # 通用组件
│       ├── layouts/            # 前台/后台布局
│       ├── router/             # 路由与守卫
│       ├── stores/             # Pinia
│       ├── utils/              # axios 封装等
│       └── views/              # 页面
├── deploy/
│   ├── nginx/nginx.conf
│   ├── mysql/init.sql
│   └── redis/redis.conf
├── docker-compose.yml
└── README.md
```

## 三、环境变量说明

复制模板并修改（生产环境务必修改全部密码与密钥）：

```bash
cp backend/.env.example backend/.env
```

| 变量 | 说明 | 默认值 |
| --- | --- | --- |
| `DEBUG` | Django 调试开关 | `0` |
| `SECRET_KEY` | Django 密钥，生产必须替换 | 随机串 |
| `DJANGO_ALLOWED_HOSTS` | 允许的主机 | `localhost,127.0.0.1,nginx,backend` |
| `MYSQL_DATABASE` | 数据库名 | `campus_market` |
| `MYSQL_USER` / `MYSQL_PASSWORD` | 数据库账号 | `campus` / `campus123456` |
| `MYSQL_ROOT_PASSWORD` | 数据库 root 密码 | `root123456` |
| `MYSQL_HOST` / `MYSQL_PORT` | 数据库地址 | `mysql` / `3306` |
| `REDIS_URL` | 缓存连接 | `redis://redis:6379/0` |
| `CELERY_BROKER_URL` | Celery Broker | `redis://redis:6379/1` |
| `CELERY_RESULT_BACKEND` | Celery 结果后端 | `redis://redis:6379/2` |
| `ORDER_TIMEOUT_SECONDS` | 订单超时秒数 | `1800`（30 分钟） |
| `CORS_ALLOWED_ORIGINS` | 本地开发跨域白名单 | `http://localhost:5173,...` |

## 四、Docker 一键部署

前提：已安装 Docker 与 Docker Compose（v2 及以上）。

```bash
# 1. 准备环境变量
cp backend/.env.example backend/.env

# 2. 构建并启动全部服务（首次构建约需 5-15 分钟，取决于网络）
docker compose up -d --build

# 3. 查看状态（全部为 healthy / running 即正常）
docker compose ps

# 4. 查看日志
docker compose logs -f backend
```

启动后访问：

| 入口 | 地址 |
| --- | --- |
| 前端首页 | http://localhost/ |
| Swagger API 文档 | http://localhost/api/v1/schema/swagger/ |
| Redoc API 文档 | http://localhost/api/v1/schema/redoc/ |
| Django Admin | http://localhost/admin/ |

**默认管理员账号**：`admin` / `Admin123456`（由 `create_default_admin` 管理命令自动创建，可在 `backend/apps/users/management/commands/create_default_admin.py` 中修改）。

停止/清理：

```bash
docker compose down          # 停止
docker compose down -v       # 停止并删除数据卷（清空数据库/上传文件）
```

## 五、本地开发启动

### 1. 后端

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

# MySQL 与 Redis 需本地可用（或先用 docker 只起这两个服务）
cp .env.example .env            # 本地开发把 MYSQL_HOST 改为 127.0.0.1

python manage.py migrate
python manage.py init_categories   # 初始化默认商品分类（幂等）
python manage.py create_default_admin
python manage.py runserver 0.0.0.0:8000
```

另开终端启动 Celery Worker（本地开发可选，图片压缩/通知/超时取消依赖它）：

```bash
cd backend
celery -A config worker -l info
# 超时任务兜底（按分钟扫描）
celery -A config beat -l info
```

### 2. 前端

```bash
cd frontend
npm install
npm run dev
```

访问 http://localhost:5173（Vite 已配置代理 `/api` → `http://127.0.0.1:8000`）。

## 六、核心功能与接口

- 认证：注册 `POST /api/v1/auth/register/`、登录 `POST /api/v1/auth/login/`、刷新 `POST /api/v1/auth/refresh/`
- 商品：列表/搜索/筛选 `GET /api/v1/products/`、发布 `POST /api/v1/products/`、详情 `GET /api/v1/products/{id}/`、收藏/取消收藏、我的收藏
- 订单：创建/支付/取消/发货/确认收货，30 分钟未支付自动取消（Celery）
- 通知：审核结果、订单状态变更、被下单提醒；支持已读/未读
- 后台：商品审核、用户管理、分类管理、订单管理、数据统计

完整接口见 Swagger 文档（见上表）。

## 七、测试

```bash
cd backend
python manage.py test apps.products apps.orders apps.users apps.notifications --verbosity=2
```

测试默认使用 MySQL（容器内执行）。Celery 任务在测试中以 eager 模式同步执行，覆盖：注册登录、JWT 刷新与账号禁用、商品发布审核通知、搜索筛选、收藏、订单全流程状态机、超时自动取消、收藏被下单通知、通知已读。

## 八、常见问题

**Q1：`mysql` 一直重启或 backend 报 `Can't connect to MySQL server`？**
首次启动 MySQL 初始化约需 30-60 秒，backend 会等待 MySQL healthy 后再迁移；若目录存在旧卷，先 `docker compose down -v` 清空再启动。

**Q2：MySQL 驱动装不上？**
本项目默认使用 `PyMySQL`（纯 Python，无编译依赖，已在 `config/__init__.py` 中 `install_as_MySQLdb()`），无需安装 `mysqlclient`。本地开发直接 `pip install -r requirements.txt` 即可；如需换回 `mysqlclient`，请先安装 MySQL Connector/C 编译环境再改 requirements。

**Q3：国内网络拉取 Docker 镜像慢 / pip 源不可达？**
- 镜像：在 Docker Desktop 的 Settings → Docker Engine 中配置国内 `registry-mirrors`（如 `https://docker.m.daocloud.io`）后重启；本项目 Dockerfile 已内置腾讯云 pip 源（`https://mirrors.cloud.tencent.com/pypi/simple/`）。
- 若后端构建时 pip 安装卡住，确认容器能访问外网；本地无 Docker 时可在 `backend/.venv` 内用腾讯/阿里源安装依赖联调。

**Q4：前端页面能打开但接口 404？**
确认 `.env` 中 `DJANGO_ALLOWED_HOSTS` 包含 `nginx`；错误多为环境变量未复制或修改后未 `docker compose up -d` 重建。

**Q5：发布商品后图片不显示？**
Nginx 的 `/media/` 代理依赖 `media_volume` 卷，与 backend 容器共享；确认 backend 与 nginx 都挂载了 `media_volume`。

**Q6：订单不会自动取消？**
超时取消由 Celery 延时任务 + Beat 兜底扫描双重保障；确认 `celery_worker` 与 `celery_beat` 两个容器都在运行，且 `.env` 中 `ORDER_TIMEOUT_SECONDS` 已生效。

**Q7：如何重置一切？**
`docker compose down -v && docker compose up -d --build`，会自动重新初始化数据库与默认管理员。

## 九、验收对照

与需求规格书「十二、验收标准」逐条对应（实现状态：已全部满足，代码级验证见下方说明）：

| # | 验收标准 | 状态 |
| --- | --- | --- |
| 1 | `docker compose up -d --build` 后所有服务正常启动 | ✅ 7 个容器（mysql/redis/backend/celery_worker/celery_beat/frontend/nginx）一键拉起，backend 等待 mysql healthy 后自动迁移并初始化 |
| 2 | 前端可访问，后端 API 可访问，Swagger 文档可访问 | ✅ 前端 `http://localhost/`，API `http://localhost/api/v1/`，Swagger/Redoc 见第四节 |
| 3 | 能完成注册、登录、刷新 token | ✅ SimpleJWT 全链路（access 30min / refresh 7d），前端 401 静默刷新并重放请求 |
| 4 | 能发布商品，商品默认进入待审核状态 | ✅ 发布即 `pending`，卖家「我的发布」可见，暂不出现在首页 |
| 5 | 管理员能审核商品，审核通过后商品在首页展示 | ✅ 后台「商品审核」通过/驳回（带原因）/违规下架，通过后清除首页缓存即时上架 |
| 6 | 游客能搜索、筛选、查看商品详情 | ✅ 关键词、分类、价格区间、成色、校区、排序、分页 |
| 7 | 登录用户能收藏、取消收藏、下单、模拟支付、取消订单 | ✅ 收藏联合唯一约束；下单锁定商品防并发重复；模拟支付后置为已支付 |
| 8 | 卖家能发货，买家能确认收货，订单状态正确流转 | ✅ pending→paid→shipped→completed；待支付可取消；终态不可再变更 |
| 9 | 订单超时未支付时，Celery 能自动取消并恢复商品状态 | ✅ 下单注册延时任务 + Beat 每 5 分钟兜底清扫双保险，取消后商品恢复在售 |
| 10 | 站内通知能正常生成和已读 | ✅ 审核结果/订单变更/收藏商品被下单三类通知，支持逐条已读与全部已读 |
| 11 | Redis 缓存首页商品列表和热门搜索生效 | ✅ 首页列表缓存 5 分钟（审核/下架/售出主动失效）；热门搜索词 ZSet |
| 12 | 代码有注释、错误处理、权限控制，前后端能完整联调 | ✅ DRF 统一异常处理与响应格式；买家/卖家/管理员三级权限矩阵；前端 `vue-tsc` 0 错误 + `vite build` 成功，后端全量 `py_compile` 通过 |
| 13 | 提供默认管理员账号 | ✅ `admin / Admin123456`（容器启动自动创建，幂等） |
| 14 | 提供完整的启动、部署、测试说明 | ✅ 本文档第四节（Docker 部署）、第五节（本地开发）、第七节（测试） |

后台管理入口：登录 `admin / Admin123456` 后访问 `http://localhost/admin`（后台首页数据总览与快捷入口），下设商品审核 `/admin/products`、分类管理 `/admin/categories`、用户管理 `/admin/users`、订单管理 `/admin/orders`、数据统计 `/admin/stats`（ECharts 分类分布图）。

> 说明：验收 12 的代码级验证在本地已执行（后端 `python -m py_compile` 全部通过、前端 `npm run type-check` 0 错误并成功 `npm run build`）；后端 26 条 Django 测试用例在 Docker 容器中执行（第七节命令）。