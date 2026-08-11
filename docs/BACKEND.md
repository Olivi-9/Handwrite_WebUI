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
3. 启动：
   ```bash
   ./scripts/run_backend.sh
   ```
   成功后访问 `http://127.0.0.1:8000/health`。

### B. Docker 运行

1. 准备 `.env`（与上同），额外填入 `TUNNEL_TOKEN`（见下方“对外暴露”）。
2. 启动（backend + cloudflared）：
   ```bash
   docker compose up -d --build
   ```
3. 手动方式（不使用 compose，仅后端）：
   ```bash
   docker build -f Dockerfile.backend -t handwrite-backend:latest .
   docker run -d \
     -p 127.0.0.1:8000:8000 \
     -v "$(pwd)/backend/static:/app/backend/static" \
     -e SESSION_SECRET_KEY="$(openssl rand -hex 32)" \
     -e CORS_ORIGINS="https://your-frontend.example.com" \
     handwrite-backend:latest
   ```

## 对外暴露（Cloudflare Tunnel）

后端**只监听 HTTP**，不再持有或申请任何证书；TLS 由 Cloudflare 边缘终止，
`cloudflared` 通过出站连接把流量送到容器，无需在防火墙上开放端口。

1. 在 Cloudflare Zero Trust → Networks → Tunnels 新建 Tunnel，复制 Token。
2. 写入 `.env`：
   ```bash
   TUNNEL_TOKEN="eyJhIjoi..."
   ```
3. 在 Tunnel 的 Public Hostname 中把域名（如 `api.example.com`）指向
   `http://backend:8000`（compose 内的服务名与端口）。
4. `docker compose up -d` 后，`cloudflared` 与后端同处 `handwrite` 网络即可连通。

`docker-compose.yml` 中后端端口只绑定在 `127.0.0.1`，用于本机调试；
**不要**把它直接发布到公网。

## 环境变量

| 变量 | 必填 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `SESSION_SECRET_KEY` | 是 | — | Session 中间件密钥，≥ 32 字符 |
| `CORS_ORIGINS` | 是 | — | 允许的前端来源（逗号分隔，禁止 `*`） |
| `BACKEND_HOST` | 否 | 本地 `127.0.0.1` / 容器 `0.0.0.0` | 监听地址 |
| `BACKEND_PORT` | 否 | `8000` | 监听端口（HTTP） |
| `TUNNEL_TOKEN` | Docker 必填 | — | Cloudflare Tunnel 令牌，供 `cloudflared` 服务使用 |
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

- Swagger UI：`http://<host>:<port>/api/docs`
- ReDoc：`http://<host>:<port>/redoc`
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
- **`backend dependencies are not installed`**：在当前 `python3`（或 `BACKEND_VENV_DIR`）里执行 `pip install -r requirements.txt`。
- **`TUNNEL_TOKEN must be set in .env`**：`docker compose` 需要 Cloudflare Tunnel 令牌，见“对外暴露”。
- **Tunnel 502 / 无法访问**：确认 Public Hostname 指向 `http://backend:8000`（不是 `https://`，也不是 `localhost`），且 `cloudflared` 与 backend 在同一 compose 网络。
