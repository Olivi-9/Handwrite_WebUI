# 前端 (Handwrite React Tailwind Frontend)

## 概述

基于 React + Vite + Tailwind CSS 的 Web UI，用于配置参数并调用后端生成手写图像。

## 技术栈

- React 18
- Vite 7
- Tailwind CSS 3
- ESLint 9（含 react-hooks / react-refresh 插件）

## 目录结构

```
frontend/handwrite-react-tailwind-frontend/
├── index.html
├── package.json
├── vite.config.js
├── tailwind.config.js
├── postcss.config.js
├── eslint.config.js
├── .env                 # 开发环境变量
├── .env.production      # 生产构建变量
└── src/
    ├── main.jsx
    ├── App.jsx
    ├── index.css
    ├── api/
    │   └── client.js    # 后端 API 调用封装
    └── components/
        ├── Fields.jsx
        └── ToggleTheme.jsx
```

## 快速开始

所有命令均在 `frontend/handwrite-react-tailwind-frontend/` 下执行。

```bash
cd frontend/handwrite-react-tailwind-frontend

# 安装依赖（pnpm 或 npm 任一）
pnpm install
# 或
npm install

# 启动开发服务器（默认 http://localhost:5173）
npm run dev

# 生产构建（输出至 dist/）
npm run build

# 本地预览生产构建
npm run preview

# 代码检查
npm run lint
```

## 环境配置

Vite 在构建时按 `mode` 选择 `.env*` 文件，仅 `VITE_` 前缀的变量会暴露给浏览器。

| 变量 | 说明 | 示例 |
| --- | --- | --- |
| `VITE_API_BASE` | 后端 API 基地址（不含尾斜杠） | `https://api.example.com:8443` |

- 开发：编辑 `.env` 让其指向本地后端（如 `https://127.0.0.1:8443`）。
- 生产：编辑 `.env.production` 指向部署后的后端域名。

修改 `.env*` 后需要重启 `vite` 进程才能生效。

## 与后端联调要点

- 后端默认 HTTPS（自签或 Let's Encrypt），开发时浏览器需先信任后端域名（在浏览器中访问一次 `https://127.0.0.1:8443/health` 并放行）。
- 后端 `CORS_ORIGINS` 必须显式包含前端开发地址，例如：
  ```
  CORS_ORIGINS="http://localhost:5173,http://127.0.0.1:5173"
  ```
- 会话基于 Cookie：除非 `CORS_ORIGINS` 含 `*`，前端 fetch 会带 credentials。

## 故障排除

- **接口报 CORS 错误**：检查后端 `.env` 的 `CORS_ORIGINS` 是否包含当前来源（精确到协议+主机+端口）。
- **`NET::ERR_CERT_AUTHORITY_INVALID`**：使用自签证书时，先手动在浏览器中访问后端地址并“继续访问”一次。
- **页面空白 / 资源 404**：确认 `VITE_API_BASE` 不含尾斜杠且协议正确；生产部署时通常由 Nginx 反向代理 `/api`。
- **构建后接口指向开发地址**：忘了维护 `.env.production`；构建命令使用 production mode。
