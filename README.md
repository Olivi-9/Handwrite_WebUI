# 手写体生成器 (Handwrite WebUI)

将文本转换为模拟手写图像的前后端分离 Web 应用。用户可在前端选择字体、背景与生成参数，由 FastAPI 后端调用 Pillow / handright 生成图像并返回。

## 项目结构

```
.
├── backend/                # FastAPI 后端
├── frontend/               # React + Vite + Tailwind 前端
├── scripts/                # 启动 / 证书申请脚本
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

```bash
# 1. 配置环境变量
cp .env.backend.example .env
# 至少填好 SESSION_SECRET_KEY 和 CORS_ORIGINS

# 2. 准备证书（容器内不会自动生成）
#    使用 Let's Encrypt：
./scripts/backend_issue_cert.sh --domain example.com --email admin@example.com
```

```bash
# 或将自签证书放到 ./certs/local/localhost.{crt,key}
openssl req -x509 -nodes -days 3650 -newkey rsa:2048 \
  -keyout local.key -out local.crt \
  -subj "/C=CN/ST=GD/L=SZ/O=Dev/OU=IT/CN=localhost"
```

# 3. 启动后端

docker compose up -d --build

# 4. 验证
```
curl -k https://127.0.0.1:8443/health
```

详细说明见 [docs/BACKEND.md](docs/BACKEND.md)。

### 二、本地开发

#### 后端

```bash
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
cp .env.backend.example .env   # 必填项

# 准备证书后启动
./scripts/run_backend_https.sh
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
