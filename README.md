# 手写体生成器 (Handwrite WebUI)

将文本转换为模拟手写图像的前后端分离 Web 应用。用户可在前端选择字体、背景与生成参数，由 FastAPI 后端调用 Pillow / handright 生成图像并返回。

## 项目结构

```
.
├── backend/                # FastAPI 后端
├── frontend/               # React + Vite + Tailwind 前端
├── scripts/                # 后端启动脚本
├── docs/
│   ├── BACKEND.md          # 后端开发与部署文档
│   └── FRONTEND.md         # 前端开发文档
├── ttf/                    # 自定义字体
├── background/             # 背景图片
├── Dockerfile.backend
├── docker-compose.yml
├── .env.backend.example    # 后端环境变量示例
└── README.md
```

## 快速开始

### 一、Docker Compose（推荐用于部署）

后端只跑 HTTP，对外访问由 Cloudflare Tunnel 穿透并终止 TLS，不再需要在服务器上申请或维护证书。

```bash
# 1. 配置环境变量
cp .env.backend.example .env
# 至少填好 SESSION_SECRET_KEY、CORS_ORIGINS 和 TUNNEL_TOKEN

# 2. 启动后端 + cloudflared
docker compose up -d --build

# 3. 验证（本机）
curl http://127.0.0.1:8000/health
```

在 Cloudflare Zero Trust 的 Tunnel 里，把 Public Hostname 指向 `http://backend:8000` 即可对外提供 HTTPS 访问。

详细说明见 [docs/BACKEND.md](docs/BACKEND.md)。

### 二、本地开发

#### 后端

```bash
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
cp .env.backend.example .env   # 必填项

./scripts/run_backend.sh       # http://127.0.0.1:8000
```

完整说明：[docs/BACKEND.md](docs/BACKEND.md)。

#### 前端

```bash
cd frontend/handwrite-react-tailwind-frontend
pnpm i
pnpm dev      # http://localhost:5173
```

完整说明：[docs/FRONTEND.md](docs/FRONTEND.md)。

## 接口约定

后端所有 API 统一返回：

```json
{ "code": 200, "message": "success", "data": {} }
```

- `code = 200` 表示成功，其余为业务错误码。
- 前端兜底文案：`请求失败，请稍后重试`。

## 文档

- [后端开发与部署指南](docs/BACKEND.md)
- [前端开发指南](docs/FRONTEND.md)

## 许可证

见 [LICENSE](LICENSE)。
