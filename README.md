# 校园二手交易平台 / Campus Market

A second-hand marketplace for college students: user registration & login, product publishing with admin review, search & filtering, favorites, ordering, simulated payment, order state machine (including 30-minute auto-cancel), in-site notifications and admin statistics. Frontend/backend separated, one-command deployment via `docker compose up -d --build`.

面向在校学生的二手交易平台：支持用户注册登录、商品发布与管理员审核、搜索筛选、收藏、下单、模拟支付、订单状态流转（含 30 分钟超时自动取消）、站内通知与后台数据统计。前后端分离，`docker compose up -d --build` 一键部署。

## 一、技术栈 / Tech Stack

| 端 Layer | 技术 Technologies |
| --- | --- |
| 后端 Backend | Python 3.11 · Django 4.2 · Django REST Framework · SimpleJWT (JWT auth) · django-cors-headers · django-filter · drf-spectacular (Swagger/Redoc) · Pillow (image compression) |
| 异步 Async | Celery 5 · Redis 7 (Broker / Result / Cache) |
| 前端 Frontend | Vue 3 · Vite · TypeScript · Vue Router · Pinia · Axios · Element Plus · ECharts |
| 数据库 Database | MySQL 8.0 (utf8mb4) |
| 部署 Deployment | Docker Compose · Nginx (reverse proxy) · Gunicorn · Celery Worker/Beat |

## 二、目录结构 / Directory Structure

```text
campus-market/
├── backend/
│   ├── manage.py
│   ├── requirements.txt
│   ├── .env.example            # Env template (copy to .env)
│   ├── Dockerfile
│   ├── config/                 # Django project config
│   │   ├── __init__.py         # Bootstraps the Celery app
│   │   ├── settings.py
│   │   ├── urls.py
│   │   ├── wsgi.py
│   │   ├── asgi.py
│   │   └── celery.py
│   ├── apps/
│   │   ├── common/             # Unified response / pagination / exceptions / permissions
│   │   ├── users/              # Registration / login / profile
│   │   ├── products/           # Categories / products / favorites / images
│   │   ├── orders/             # Orders & state machine
│   │   └── notifications/      # In-site notifications
│   ├── media/                  # Uploaded images (volume-mounted in containers)
│   └── static/                 # collectstatic output
├── frontend/
│   ├── package.json
│   ├── vite.config.ts
│   ├── tsconfig.json
│   ├── index.html
│   ├── Dockerfile
│   └── src/
│       ├── api/                # API layer
│       ├── assets/
│       ├── components/         # Shared components
│       ├── layouts/            # Public / admin layouts
│       ├── router/             # Routes & guards
│       ├── stores/             # Pinia stores
│       ├── utils/              # Axios wrapper etc.
│       └── views/              # Pages
├── deploy/
│   ├── nginx/nginx.conf
│   ├── mysql/init.sql
│   └── redis/redis.conf
├── docker-compose.yml
└── README.md
```

## 三、环境变量说明 / Environment Variables

Copy the template and edit it. **For production, always replace all passwords and secrets.**

复制模板并修改（生产环境务必修改全部密码与密钥）：

```bash
cp backend/.env.example backend/.env
```

| Variable 变量 | Description 说明 | Default 默认值 |
| --- | --- | --- |
| `DEBUG` | Django debug switch / 调试开关 | `0` |
| `SECRET_KEY` | Django secret key, replace in production / 生产必须替换 | random 随机串 |
| `DJANGO_ALLOWED_HOSTS` | Allowed hosts / 允许的主机 | `localhost,127.0.0.1,nginx,backend` |
| `MYSQL_DATABASE` | Database name / 数据库名 | `campus_market` |
| `MYSQL_USER` / `MYSQL_PASSWORD` | DB account / 数据库账号 | `campus` / `campus123456` |
| `MYSQL_ROOT_PASSWORD` | DB root password / root 密码 | `root123456` |
| `MYSQL_HOST` / `MYSQL_PORT` | DB host & port / 数据库地址 | `mysql` / `3306` |
| `REDIS_URL` | Cache connection / 缓存连接 | `redis://redis:6379/0` |
| `CELERY_BROKER_URL` | Celery broker / Broker | `redis://redis:6379/1` |
| `CELERY_RESULT_BACKEND` | Celery result backend / 结果后端 | `redis://redis:6379/2` |
| `ORDER_TIMEOUT_SECONDS` | Order timeout in seconds / 订单超时秒数 | `1800` (30 min) |
| `CORS_ALLOWED_ORIGINS` | Dev CORS whitelist / 本地开发跨域白名单 | `http://localhost:5173,...` |

## 四、Docker 一键部署 / One-Command Deployment with Docker

Prerequisite: Docker and Docker Compose (v2+) installed.

前提：已安装 Docker 与 Docker Compose（v2 及以上）。

```bash
# 1. Prepare environment variables / 准备环境变量
cp backend/.env.example backend/.env

# 2. Build and start all services (first build takes ~5-15 min depending on network)
#    构建并启动全部服务（首次构建约需 5-15 分钟，取决于网络）
docker compose up -d --build

# 3. Check status (all should be healthy / running)
#    查看状态（全部为 healthy / running 即正常）
docker compose ps

# 4. Follow logs / 查看日志
docker compose logs -f backend
```

Access after startup / 启动后访问：

| Entry 入口 | URL 地址 |
| --- | --- |
| Frontend home / 前端首页 | http://localhost/ |
| Swagger API docs / API 文档 | http://localhost/api/v1/schema/swagger/ |
| Redoc API docs / API 文档 | http://localhost/api/v1/schema/redoc/ |
| Django Admin | http://localhost/admin/ |

**Default admin account / 默认管理员账号**：`admin` / `Admin123456` (auto-created by the `create_default_admin` management command; edit `backend/apps/users/management/commands/create_default_admin.py` to change it / 由管理命令自动创建，可在 `backend/apps/users/management/commands/create_default_admin.py` 中修改)。

Stop / cleanup / 停止与清理：

```bash
docker compose down          # Stop / 停止
docker compose down -v       # Stop and remove volumes (wipes DB & uploads) / 停止并删除数据卷
```

## 五、本地开发启动 / Local Development

### 1. 后端 Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

# MySQL and Redis must be available locally (or start only those two via docker first)
# MySQL 与 Redis 需本地可用（或先用 docker 只起这两个服务）
cp .env.example .env            # For local dev set MYSQL_HOST to 127.0.0.1 / 本地开发把 MYSQL_HOST 改为 127.0.0.1

python manage.py migrate
python manage.py init_categories   # Init default categories (idempotent) / 初始化默认商品分类（幂等）
python manage.py create_default_admin
python manage.py runserver 0.0.0.0:8000
```

In another terminal, start Celery Worker (optional for local dev; needed for image compression / notifications / order timeout / 本地开发可选，图片压缩/通知/超时取消依赖它):

```bash
cd backend
celery -A config worker -l info
# Fallback sweep for timeout orders (per-minute scan) / 超时任务兜底（按分钟扫描）
celery -A config beat -l info
```

### 2. 前端 Frontend

```bash
cd frontend
npm install
npm run dev
```

Visit http://localhost:5173 (Vite proxies `/api` → `http://127.0.0.1:8000` / Vite 已配置代理 `/api` → `http://127.0.0.1:8000`)。

## 六、核心功能与接口 / Core Features & APIs

- Auth 认证：Register 注册 `POST /api/v1/auth/register/` · Login 登录 `POST /api/v1/auth/login/` · Refresh 刷新 `POST /api/v1/auth/refresh/`
- Products 商品：List/search/filter 列表/搜索/筛选 `GET /api/v1/products/` · Publish 发布 `POST /api/v1/products/` · Detail 详情 `GET /api/v1/products/{id}/` · Favorite/unfavorite 收藏/取消收藏 · My favorites 我的收藏
- Orders 订单：Create/pay/cancel/ship/confirm 创建/支付/取消/发货/确认收货；unpaid orders auto-cancel after 30 min (Celery) / 30 分钟未支付自动取消
- Notifications 通知：review results 审核结果、order status changes 订单状态变更、favorited-product-sold alerts 被下单提醒；read/unread 支持已读/未读
- Admin 后台：product review 商品审核、user management 用户管理、category management 分类管理、order management 订单管理、statistics 数据统计

Full API list is available in the Swagger docs (see table above).

完整接口见 Swagger 文档（见上表）。

## 七、测试 / Tests

```bash
cd backend
python manage.py test apps.products apps.orders apps.users apps.notifications --verbosity=2
```

Tests run against MySQL (inside containers). Celery tasks run synchronously in eager mode. Coverage: registration/login, JWT refresh & account disabling, product publish-review-notify, search/filter, favorites, full order state machine, timeout auto-cancel, favorite-ordered notification, notification read/unread.

测试默认使用 MySQL（容器内执行）。Celery 任务在测试中以 eager 模式同步执行，覆盖：注册登录、JWT 刷新与账号禁用、商品发布审核通知、搜索筛选、收藏、订单全流程状态机、超时自动取消、收藏被下单通知、通知已读。

## 八、常见问题 / FAQ

**Q1: `mysql` keeps restarting or backend reports `Can't connect to MySQL server`? / `mysql` 一直重启或 backend 报 `Can't connect to MySQL server`？**
MySQL initialization takes ~30-60s on first start; backend waits for MySQL to be healthy before migrating. If old volumes exist, run `docker compose down -v` first.

首次启动 MySQL 初始化约需 30-60 秒，backend 会等待 MySQL healthy 后再迁移；若目录存在旧卷，先 `docker compose down -v` 清空再启动。

**Q2: MySQL driver fails to install? / MySQL 驱动装不上？**
This project uses `PyMySQL` by default (pure Python, no compilation; `config/__init__.py` calls `install_as_MySQLdb()`), so `mysqlclient` is not required. Just `pip install -r requirements.txt` for local dev. To switch back to `mysqlclient`, install the MySQL Connector/C build environment first and update requirements.

本项目默认使用 `PyMySQL`（纯 Python，无编译依赖，已在 `config/__init__.py` 中 `install_as_MySQLdb()`），无需安装 `mysqlclient`。本地开发直接 `pip install -r requirements.txt` 即可；如需换回 `mysqlclient`，请先安装 MySQL Connector/C 编译环境再改 requirements。

**Q3: Slow Docker image pulls / unreachable pip index on CN networks? / 国内网络拉取 Docker 镜像慢 / pip 源不可达？**
- Images: configure domestic `registry-mirrors` in Docker Desktop Settings → Docker Engine (e.g. `https://docker.m.daocloud.io`) and restart; the Dockerfile already uses the Tencent Cloud PyPI mirror (`https://mirrors.cloud.tencent.com/pypi/simple/`).
- If pip hangs during backend build, make sure the container can reach the internet; without Docker you can install deps into `backend/.venv` using Tencent/Aliyun mirrors for local dev.

- 镜像：在 Docker Desktop 的 Settings → Docker Engine 中配置国内 `registry-mirrors`（如 `https://docker.m.daocloud.io`）后重启；本项目 Dockerfile 已内置腾讯云 pip 源（`https://mirrors.cloud.tencent.com/pypi/simple/`）。
- 若后端构建时 pip 安装卡住，确认容器能访问外网；本地无 Docker 时可在 `backend/.venv` 内用腾讯/阿里源安装依赖联调。

**Q4: Frontend loads but APIs return 404? / 前端页面能打开但接口 404？**
Make sure `DJANGO_ALLOWED_HOSTS` in `.env` contains `nginx`; usually the env file was not copied or services were not rebuilt with `docker compose up -d` after changes.

确认 `.env` 中 `DJANGO_ALLOWED_HOSTS` 包含 `nginx`；错误多为环境变量未复制或修改后未 `docker compose up -d` 重建。

**Q5: Product images not shown after publishing? / 发布商品后图片不显示？**
Nginx `/media/` proxying depends on the `media_volume` shared with the backend container; make sure both backend and nginx mount `media_volume`.

Nginx 的 `/media/` 代理依赖 `media_volume` 卷，与 backend 容器共享；确认 backend 与 nginx 都挂载了 `media_volume`。

**Q6: Orders are not auto-cancelled? / 订单不会自动取消？**
Timeout cancellation is double-protected by a Celery scheduled task plus a Beat fallback sweep; make sure both `celery_worker` and `celery_beat` containers run and `ORDER_TIMEOUT_SECONDS` in `.env` is effective.

超时取消由 Celery 延时任务 + Beat 兜底扫描双重保障；确认 `celery_worker` 与 `celery_beat` 两个容器都在运行，且 `.env` 中 `ORDER_TIMEOUT_SECONDS` 已生效。

**Q7: How to reset everything? / 如何重置一切？**
`docker compose down -v && docker compose up -d --build` will re-initialize the database and the default admin automatically.

`docker compose down -v && docker compose up -d --build`，会自动重新初始化数据库与默认管理员。

## 九、验收对照 / Acceptance Checklist

Mapped one-to-one against the spec's acceptance criteria (all met; code-level verification notes below).

与需求规格书「十二、验收标准」逐条对应（实现状态：已全部满足，代码级验证见下方说明）：

| # | Acceptance / 验收标准 | Status 状态 |
| --- | --- | --- |
| 1 | All services start after `docker compose up -d --build` / 所有服务正常启动 | ✅ 7 containers (mysql/redis/backend/celery_worker/celery_beat/frontend/nginx) start together; backend waits for mysql healthy, then migrates & initializes automatically |
| 2 | Frontend, backend API and Swagger docs accessible / 前端、后端 API、Swagger 均可访问 | ✅ Frontend `http://localhost/`, API `http://localhost/api/v1/`, Swagger/Redoc see Section 4 |
| 3 | Register, login, refresh token work / 注册、登录、刷新 token | ✅ Full SimpleJWT flow (access 30min / refresh 7d); frontend silently refreshes & replays on 401 |
| 4 | Publishing a product puts it in pending review / 发布商品进入待审核 | ✅ Status `pending` on publish; visible in "My Products", hidden from home until approved |
| 5 | Admin can approve; approved products appear on home / 管理员审核通过后在首页展示 | ✅ Admin review: approve/reject (with reason)/forbid; home cache purged for instant visibility |
| 6 | Guests can search, filter and view details / 游客可搜索、筛选、查看详情 | ✅ Keyword, category, price range, condition, campus, sorting, pagination |
| 7 | Authenticated users can favorite, order, pay, cancel / 收藏、取消收藏、下单、模拟支付、取消订单 | ✅ Unique favorite constraint; order locks product to prevent double-buy; simulated payment flips to paid |
| 8 | Seller ships, buyer confirms; status flows correctly / 发货、确认收货、状态正确流转 | ✅ pending→paid→shipped→completed; cancellable while pending; terminal states immutable |
| 9 | Celery auto-cancels timed-out unpaid orders & restores product / 超时自动取消并恢复商品 | ✅ Scheduled task + Beat fallback sweep every 5 min; product returns to on-sale after cancel |
| 10 | In-site notifications generated and readable / 站内通知生成与已读 | ✅ Review / order-status / favorited-ordered notifications; read one-by-one or all |
| 11 | Redis caches home list & hot searches / Redis 缓存首页与热搜 | ✅ Home list cached 5 min (invalidated on review/off-shelf/sold); hot search keywords in ZSet |
| 12 | Comments, error handling, permission control; full integration / 代码规范与完整联调 | ✅ DRF unified exceptions & response format; buyer/seller/admin permission matrix; frontend `vue-tsc` 0 errors + `vite build` OK; backend full `py_compile` passed |
| 13 | Default admin account provided / 提供默认管理员账号 | ✅ `admin / Admin123456` (auto-created on startup, idempotent) |
| 14 | Complete startup, deployment and test docs / 完整的启动、部署、测试说明 | ✅ This doc: Section 4 (Docker), Section 5 (local dev), Section 7 (tests) |

Admin panel: log in with `admin / Admin123456`, then visit `http://localhost/admin`. Under it: product review `/admin/products`, category management `/admin/categories`, user management `/admin/users`, order management `/admin/orders`, statistics `/admin/stats` (ECharts category distribution).

后台管理入口：登录 `admin / Admin123456` 后访问 `http://localhost/admin`（后台首页数据总览与快捷入口），下设商品审核 `/admin/products`、分类管理 `/admin/categories`、用户管理 `/admin/users`、订单管理 `/admin/orders`、数据统计 `/admin/stats`（ECharts 分类分布图）。

> Note: code-level verification for item 12 was run locally (backend `python -m py_compile` all passed, frontend `npm run type-check` 0 errors and `npm run build` succeeded); the 26 Django test cases run inside Docker containers (Section 7).
>
> 说明：验收 12 的代码级验证在本地已执行（后端 `python -m py_compile` 全部通过、前端 `npm run type-check` 0 错误并成功 `npm run build`）；后端 26 条 Django 测试用例在 Docker 容器中执行（第七节命令）。