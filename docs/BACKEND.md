# 后端 (Handwrite Generator API)

## 概述

基于 FastAPI 的手写体生成服务，提供文本→手写图像的 HTTP API。

## 技术栈

- Python 3.12+
- FastAPI / Uvicorn / Starlette
- Pillow（图像处理）
- handright（手写笔迹模拟）
- 完整依赖见 [`requirements.txt`](../requirements.txt)

## 目录结构

```
backend/
├── main.py              # FastAPI 应用入口、中间件、异常处理
├── core/
│   ├── api.py           # 统一响应格式 (code/message/data)
│   ├── cleanup.py       # 上传/输出目录定期清理
│   ├── generator.py     # 手写图像生成核心逻辑
│   ├── logging_config.py# 日志配置
│   ├── settings.py      # 环境变量加载、路径常量
│   └── utils.py
├── routers/
│   ├── backgrounds.py   # /api/backgrounds
│   ├── fonts.py         # /api/fonts
│   ├── generate.py      # /api/generate
│   └── upload.py        # /api/upload
└── static/              # uploads/ 与 output/ 运行时目录
```

## 快速开始

### A. 本地运行（非容器）

1. 准备 Python 3.12+ 环境，安装依赖：
   ```bash
   python3 -m venv .venv
   . .venv/bin/activate
   pip install -r requirements.txt
   ```
2. 复制环境变量示例并编辑：
   ```bash
   cp .env.backend.example .env
   # 至少填好 SESSION_SECRET_KEY 与 CORS_ORIGINS
   ```
3. 准备证书（三种方式选一种，见下方“证书配置”）。
4. 启动：
   ```bash
   ./scripts/run_backend_https.sh
   ```
   成功后访问 `https://127.0.0.1:8443/health`。

### B. Docker 运行

1. 准备 `.env`（与上同）。
2. 生成证书（**必须在容器外完成**）：
   ```bash
   ./scripts/backend_issue_cert.sh --domain example.com --email admin@example.com
   # 或自带本地证书放到 ./certs/local/
   ```
3. 启动：
   ```bash
   docker compose up -d --build
   ```
4. 手动方式（不使用 compose）：
   ```bash
   docker build -f Dockerfile.backend -t handwrite-backend:latest .
   docker run -d \
     -p 8443:8443 \
     -v "$(pwd)/certs:/app/certs:ro" \
     -v "$(pwd)/backend/static:/app/backend/static" \
     -e SESSION_SECRET_KEY="$(openssl rand -hex 32)" \
     -e CORS_ORIGINS="https://your-frontend.example.com" \
     -e BACKEND_SSL_CERT_FILE=/app/certs/letsencrypt/live/example.com/fullchain.pem \
     -e BACKEND_SSL_KEY_FILE=/app/certs/letsencrypt/live/example.com/privkey.pem \
     handwrite-backend:latest
   ```

## 证书配置

`scripts/run_backend_https.sh` 按以下优先级查找证书，**不会自动生成**：

1. **手动指定**：环境变量 `BACKEND_SSL_CERT_FILE` 与 `BACKEND_SSL_KEY_FILE`。
2. **Let's Encrypt**：`${LETSENCRYPT_DIR}/live/${BACKEND_DOMAIN}/{fullchain,privkey}.pem`，默认根目录为 `./certs/letsencrypt`。
3. **本地开发证书**：`./certs/local/localhost.{crt,key}`，必须事先存在。

若三种都没找到，脚本会输出明确错误并退出。生成本地开发证书的一次性命令：

```bash
mkdir -p ./certs/local
openssl req -x509 -nodes -newkey rsa:2048 \
  -keyout ./certs/local/localhost.key \
  -out   ./certs/local/localhost.crt \
  -days 365 -subj "/CN=localhost" \
  -addext "subjectAltName=DNS:localhost,IP:127.0.0.1"
```

申请 Let's Encrypt 证书：

```bash
./scripts/backend_issue_cert.sh --domain api.example.com --email admin@example.com
```

## 环境变量

| 变量 | 必填 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `SESSION_SECRET_KEY` | 是 | — | Session 中间件密钥，≥ 32 字符 |
| `CORS_ORIGINS` | 是 | — | 允许的前端来源（逗号分隔，禁止 `*`） |
| `BACKEND_HOST` | 否 | `0.0.0.0` | 监听地址 |
| `BACKEND_PORT` | 否 | `8443` | 监听端口 |
| `BACKEND_DOMAIN` | 否 | `localhost` | 用于定位 Let's Encrypt 证书目录 |
| `BACKEND_SSL_CERT_FILE` | 否 | — | 手动指定证书路径 |
| `BACKEND_SSL_KEY_FILE` | 否 | — | 手动指定私钥路径 |
| `LETSENCRYPT_DIR` | 否 | `./certs/letsencrypt` | Let's Encrypt 输出根目录 |
| `LETSENCRYPT_DOMAIN` | 否 | — | 申请证书的主域名 |
| `LETSENCRYPT_EMAIL` | 否 | — | Let's Encrypt 联系邮箱 |
| `CERTBOT_WEBROOT` | 否 | `./certs/www` | webroot 模式下的 ACME 验证目录 |
| `LOCAL_CERT_DIR` | 否 | `./certs/local` | 本地证书目录 |
| `BACKEND_VENV_DIR` | 否 | `./.venv` | 本地启动脚本使用的虚拟环境 |
| `BACKEND_LOG_LEVEL` | 否 | `INFO` | 日志级别 |
| `BACKEND_LOG_DIR` | 否 | `backend/logs` | 日志目录 |
| `BACKEND_LOG_FILE` | 否 | `backend.log` | 日志文件名 |
| `BACKEND_LOG_MAX_BYTES` | 否 | `10485760` | 单文件最大字节数 |
| `BACKEND_LOG_BACKUP_COUNT` | 否 | `5` | 日志轮转保留份数 |
| `CLEANUP_INTERVAL_SECONDS` | 否 | `1200` | 清理循环间隔 |
| `FILE_RETENTION_SECONDS` | 否 | `1200` | 文件保留时长 |
| `HANDWRITE_WORKERS` | 否 | CPU 核数 | 生成任务并发数上限 |

完整示例见仓库根目录 [`.env.backend.example`](../.env.backend.example)。

## API 文档

启动后端后访问：

- Swagger UI：`https://<host>:<port>/docs`
- ReDoc：`https://<host>:<port>/redoc`
- 健康检查：`GET /health` → `{"code":200,"message":"success","data":{"status":"ok"}}`

所有业务接口统一返回：

```json
{ "code": 200, "message": "success", "data": {} }
```

## 开发说明

- 新增接口：在 `backend/routers/` 下新建模块，使用 `APIRouter`，然后在 `backend/main.py` 中 `include_router(..., prefix="/api")`。
- 错误处理：抛出 `backend.core.api.AppError`，由全局处理器统一封装。
- 资源目录：`ttf/`（字体）、`background/`（背景）由 `core/settings.py` 中的常量定位，可通过文件系统直接增删。

## 故障排除

- **`SESSION_SECRET_KEY must be set …`**：`.env` 中未配置或长度 < 32。
- **`CORS_ORIGINS must declare at least one allowed origin`**：必须显式列出前端来源，禁止 `*`。
- **`no HTTPS certificate found`**：见“证书配置”三种方式之一。
- **`backend dependencies are not installed`**：在当前 `python3`（或 `BACKEND_VENV_DIR`）里执行 `pip install -r requirements.txt`。
- **Docker 健康检查失败**：通常是证书路径或卷挂载不一致，确认 `BACKEND_SSL_CERT_FILE` 指向容器内路径（默认 `/app/certs/...`）。
