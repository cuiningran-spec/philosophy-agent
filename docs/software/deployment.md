# ThinkLab 阿里云 ECS 部署记录

> 本文记录 ThinkLab 从本地项目到阿里云 ECS 公网部署的完整过程，包括环境准备、项目上传、前后端部署、数据库配置、Nginx 反向代理、DeepSeek API 配置、故障排查以及 systemd 服务管理。
>
> **当前部署方式：** Ubuntu 22.04 + Python 虚拟环境 + Node.js + Nginx + systemd  
> **部署时间：** 2026 年 11 月  
> **项目目录：** `/root/philosophy-agent`

---

## 一、项目部署架构

ThinkLab 是一个基于大语言模型的哲学对话 Agent 项目，采用前后端分离的架构。

### 1. 技术栈

| 模块 | 技术 |
|---|---|
| 云服务器 | 阿里云 ECS |
| 操作系统 | Ubuntu 22.04 |
| 后端框架 | FastAPI |
| 后端运行环境 | Python 3.10 + venv |
| 前端框架 | React + TypeScript + Vite |
| 前端服务 | Node.js + Express |
| Web 服务器 | Nginx |
| 数据库 | SQLite（当前实际运行配置） |
| 向量存储 | Local VectorStore |
| 大语言模型 | DeepSeek |
| 服务管理 | systemd |

### 2. 部署架构

```text
                   用户浏览器
                       |
                       | HTTP :80
                       v
                 Nginx Web Server
                       |
                       v
              Node.js / Express
                 前端服务 :4173
                       |
                       | /api 请求转发
                       v
                FastAPI Backend
                   :8000
                       |
          +------------+------------+
          |            |            |
          v            v            v
       SQLite      VectorStore   DeepSeek API
       数据库       本地向量存储   大语言模型
```

其中：

- Nginx 负责接收公网 HTTP 请求。
- Node.js 提供前端页面，并将 `/api` 请求转发给 FastAPI。
- FastAPI 负责处理业务逻辑、Agent 调用和数据读写。
- DeepSeek 提供大语言模型能力。
- SQLite 和本地向量存储用于当前 MVP 阶段的数据管理。

### 3. 端口规划

| 服务 | 端口 | 监听地址 | 用途 |
|---|---:|---|---|
| Nginx | 80 | `0.0.0.0` | 公网 HTTP 入口 |
| Node.js | 4173 | `127.0.0.1`（建议后续调整） | 前端服务 |
| FastAPI | 8000 | `127.0.0.1` | 后端 API |
| PostgreSQL | 5432 | 未启用 | 预留数据库端口 |

公网只需要开放 80 端口。4173、8000 和 5432 不应直接对公网开放。

---

## 二、云服务器环境准备

### 1. 创建 ECS 实例

在阿里云控制台创建 ECS 云服务器，选择：

- 操作系统：Ubuntu 22.04
- 登录方式：root 用户，通过 ECS Workbench 登录
- 网络：配置公网 IP
- 安全组：开放 TCP 80 端口

安全组中的 80 端口用于网站访问。

不建议将数据库端口、后端端口和前端内部端口直接开放给公网。

### 2. 安装 Git

在 ECS 终端执行：

```bash
apt update
apt install -y git
```

验证：

```bash
git --version
```

### 3. 安装 Docker

执行：

```bash
apt install -y docker.io docker-compose-v2
```

启动 Docker：

```bash
systemctl enable --now docker
```

检查：

```bash
docker --version
docker compose version
```

**说明：** Docker 已安装，但本次最终运行的前后端服务并没有使用 Docker Compose。

### 4. 安装 Python 环境

安装 Python 和虚拟环境工具：

```bash
apt install -y python3 python3-venv python3-pip
```

检查：

```bash
python3 --version
```

本次服务器实际使用 Python 3.10.12。

### 5. 安装 Node.js

使用 NodeSource 安装 Node.js 20：

```bash
curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
apt install -y nodejs
```

检查：

```bash
node -v
npm -v
```

本次实际安装的是 Node.js 20。

### 6. 安装 Nginx

```bash
apt install -y nginx
systemctl enable --now nginx
```

检查：

```bash
nginx -v
systemctl status nginx
```

---

## 三、上传项目到 ECS

### 1. 最初尝试 Git Clone

原计划直接从 GitHub 克隆项目：

```bash
git clone https://github.com/cuiningran-spec/philosophy-agent.git
```

但是执行时遇到了网络连接超时，ECS 无法正常连接 GitHub。

### 2. 最终解决方法：ZIP 上传

由于 Git Clone 无法正常完成，改为：

1. 在本地电脑打开 GitHub 仓库。
2. 下载项目 ZIP 压缩包。
3. 将 ZIP 文件上传到 ECS。
4. 在服务器解压项目。

项目最终存放在：

```text
/root/philosophy-agent
```

项目关键目录：

```text
philosophy-agent/
├── code/
│   ├── backend/
│   ├── frontend/
│   ├── core_engine/
│   ├── tests/
│   └── ...
├── docs/
├── tests/
└── ...
```

### 3. 解压项目

如果 ZIP 文件已上传到服务器，可以使用：

```bash
apt install -y unzip
unzip 项目压缩包.zip -d /root/
```

根据实际解压结果确认项目目录。

---

## 四、后端部署

### 1. 创建 Python 虚拟环境

进入项目目录：

```bash
cd /root/philosophy-agent/code
```

创建虚拟环境：

```bash
python3 -m venv .venv
```

激活环境：

```bash
source .venv/bin/activate
```

### 2. 安装 Python 依赖

进入后端目录：

```bash
cd /root/philosophy-agent/code/backend
```

安装依赖：

```bash
pip install -r requirements.txt
```

如果项目依赖文件位置不同，需要根据实际项目结构调整。

### 3. 配置后端运行环境

后端启动时需要从 `code/backend` 目录执行，并通过 `PYTHONPATH=.` 使项目模块能够正确导入。

最终启动命令：

```bash
cd /root/philosophy-agent/code/backend

PYTHONPATH=. ../.venv/bin/python -m uvicorn app.main:app \
  --host 127.0.0.1 \
  --port 8000
```

后端监听本机 8000 端口，不直接暴露给公网。

---

## 五、前端部署

### 1. 安装前端依赖

进入前端目录：

```bash
cd /root/philosophy-agent/code/frontend
```

安装依赖：

```bash
npm ci
```

### 2. 构建前端

执行：

```bash
npm run build
```

构建成功后生成：

```text
frontend/dist/
```

该目录保存 Vite 构建后的前端静态资源。

### 3. 启动 Express 服务

本项目通过 Express 提供前端页面，并代理后端 API 请求。

最终使用的启动命令：

```bash
cd /root/philosophy-agent/code/frontend

PORT=4173 \
AGENT_API_BASE=http://127.0.0.1:8000 \
npm run server
```

其中：

- `PORT=4173`：指定前端服务端口。
- `AGENT_API_BASE`：指定 FastAPI 后端地址。

---

## 六、数据库部署及问题处理

### 1. 原计划使用 PostgreSQL

项目中提供了 Docker Compose 配置，原计划使用 PostgreSQL 16。

但执行 Docker Compose 启动数据库时出现错误：

```text
failed to resolve reference "docker.io/library/postgres:16"

dial tcp ...:443: i/o timeout
```

原因是 ECS 无法正常连接 Docker Hub，导致 PostgreSQL 镜像拉取失败。

### 2. 最终解决方法

考虑到当前项目处于 MVP 阶段，并且后端配置中：

```env
THINKLAB_DB_MODE=auto
```

因此采用了自动回退方案，使用 SQLite 运行。

数据库文件位置：

```text
/root/philosophy-agent/code/backend/.cache/thinklab.db
```

向量存储使用本地模式：

```env
THINKLAB_VECTORSTORE_MODE=local
```

**注意：** 当前正式运行的是 SQLite，而不是 PostgreSQL。后续如果迁移到 PostgreSQL，需要重新配置数据库连接、迁移数据并验证业务功能。

---

## 七、DeepSeek API 配置

### 1. 创建环境变量文件

在以下位置配置环境变量：

```text
/root/philosophy-agent/code/.env
```

配置内容：

```env
THINKLAB_LLM_MODE=deepseek
THINKLAB_LLM_FALLBACK=false
THINKLAB_DB_MODE=auto
THINKLAB_VECTORSTORE_MODE=local

DEEPSEEK_API_KEY=填写自己的真实API_KEY
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat
```

其中：

- `THINKLAB_LLM_MODE`：指定大语言模型运行模式。
- `THINKLAB_LLM_FALLBACK`：控制是否允许回退。
- `THINKLAB_DB_MODE`：数据库运行模式。
- `THINKLAB_VECTORSTORE_MODE`：向量存储模式。
- `DEEPSEEK_API_KEY`：DeepSeek API 密钥。
- `DEEPSEEK_BASE_URL`：DeepSeek API 地址。
- `DEEPSEEK_MODEL`：使用的模型名称。

### 2. API Key 安全要求

真实 API Key 只能保存在服务器的环境变量文件中。

不要：

- 上传真实 `.env` 文件到 GitHub。
- 将 API Key 写进前端代码。
- 将 API Key 提交到公开仓库。
- 在公开截图中暴露 API Key。

可以通过以下命令检查是否填写了 API Key，但不要打印真实密钥：

```bash
if grep -q '^DEEPSEEK_API_KEY=.' /root/philosophy-agent/code/.env; then
    echo "API Key 已填写"
else
    echo "API Key 未填写"
fi
```

### 3. 后端启动日志验证

后端日志曾显示：

```text
LLM 已就绪：deepseek / model=deepseek-chat
ThinkLabAgent 初始化：llm_mode=deepseek
知识库预热完成
Application startup complete.
```

这说明后端已经成功读取 DeepSeek 配置并初始化模型。

仍应通过网站实际发送对话请求，确认模型 API 调用正常。

---

## 八、Nginx 反向代理配置

### 1. Nginx 的作用

用户访问 ECS 公网 IP 时，请求首先到达 Nginx。

Nginx 再将请求转发给本机的 Node.js 前端服务。

### 2. 配置文件

本次使用 Nginx 默认站点配置进行反向代理。

配置文件：

```text
/etc/nginx/sites-available/default
```

配置示例：

```nginx
server {
    listen 80 default_server;
    listen [::]:80 default_server;

    server_name _;

    location / {
        proxy_pass http://127.0.0.1:4173;

        proxy_http_version 1.1;

        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

如果项目需要 SSE 流式响应，应根据实际代理链路进一步检查缓冲配置，必要时对相关 API 路径关闭代理缓冲。

### 3. 检查配置

```bash
nginx -t
```

如果显示：

```text
syntax is ok
test is successful
```

说明配置语法正确。

重载 Nginx：

```bash
systemctl reload nginx
```

---

## 九、首次启动与后台运行

最初没有使用 systemd，而是使用 `nohup` 将前后端进程放在后台运行。

### 1. 后端启动

```bash
cd /root/philosophy-agent/code/backend

nohup env PYTHONPATH=. \
../.venv/bin/python -m uvicorn app.main:app \
--host 127.0.0.1 \
--port 8000 \
> ../logs/backend.log 2>&1 < /dev/null &
```

### 2. 前端启动

```bash
cd /root/philosophy-agent/code/frontend

nohup env PORT=4173 \
AGENT_API_BASE=http://127.0.0.1:8000 \
npm run server \
> ../logs/frontend.log 2>&1 < /dev/null &
```

### 3. 首次访问成功

通过公网 IP 访问网站，ThinkLab 首页可以正常打开。

此时部署已经基本完成，但服务管理仍然存在不足。

---

## 十、部署过程中遇到的主要问题

### 问题一：GitHub 克隆项目超时

**现象：**

```text
git clone https://github.com/cuiningran-spec/philosophy-agent.git
```

执行失败，提示连接超时。

**原因：**

ECS 无法正常连接 GitHub。

**解决方法：**

改为本地下载 GitHub ZIP，再上传到 ECS 解压。

---

### 问题二：Docker Compose 无法拉取 PostgreSQL 镜像

**现象：**

```text
failed to resolve reference "docker.io/library/postgres:16"
```

**原因：**

ECS 无法正常连接 Docker Hub，导致 PostgreSQL 镜像拉取失败。

**解决方法：**

暂时放弃 PostgreSQL 容器部署，利用项目的自动数据库回退机制，改用 SQLite。

**最终状态：**

- Docker 已安装。
- PostgreSQL 容器未成功启动。
- ThinkLab 使用 SQLite 正常运行。

---

### 问题三：网站出现 502 Bad Gateway

**现象：**

浏览器访问网站时显示：

```text
502 Bad Gateway

nginx/1.18.0 (Ubuntu)
```

**排查过程：**

执行：

```bash
ps aux | grep -E 'uvicorn|server/index.mjs' | grep -v grep
```

检查端口：

```bash
ss -lntp | grep -E ':80|:4173|:8000'
```

发现：

- Nginx 的 80 端口正常。
- FastAPI 的 8000 端口正常。
- Node.js 的 4173 端口没有监听。

**原因：**

Node 前端服务已经停止，而 Nginx 仍然尝试将请求转发到 4173 端口。

**临时解决方法：**

重新启动前端：

```bash
cd /root/philosophy-agent/code/frontend

nohup env PORT=4173 \
AGENT_API_BASE=http://127.0.0.1:8000 \
npm run server \
> ../logs/frontend.log 2>&1 < /dev/null &
```

之后网站恢复正常。

**进一步分析：**

`nohup` 只能让进程在后台运行，并不能保证进程异常退出后自动重启，也不能自动管理 ECS 重启后的服务启动。

因此，最终决定使用 systemd 管理前后端。

---

## 十一、最终解决方案：systemd 服务管理

这是本次部署中最重要的后续优化。

### 1. 为什么使用 systemd？

systemd 是 Ubuntu 的系统服务管理工具。

相比手动使用 `nohup`，它可以：

- 设置服务开机自动启动。
- 服务意外退出后自动尝试重启。
- 统一查看服务状态。
- 统一查看运行日志。
- 使用标准命令启动、停止和重启服务。

### 2. 创建后端服务

创建：

```text
/etc/systemd/system/thinklab-backend.service
```

内容：

```ini
[Unit]
Description=ThinkLab FastAPI Backend
After=network.target

[Service]
Type=simple
WorkingDirectory=/root/philosophy-agent/code/backend
Environment=PYTHONPATH=.
ExecStart=/root/philosophy-agent/code/.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

### 3. 创建前端服务

首先获取 npm 路径：

```bash
command -v npm
```

创建：

```text
/etc/systemd/system/thinklab-frontend.service
```

本次使用的配置：

```ini
[Unit]
Description=ThinkLab Node Frontend
After=network.target thinklab-backend.service
Wants=thinklab-backend.service

[Service]
Type=simple
WorkingDirectory=/root/philosophy-agent/code/frontend
Environment=PORT=4173
Environment=AGENT_API_BASE=http://127.0.0.1:8000
ExecStart=/usr/bin/npm run server
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

注意：`ExecStart` 中的 npm 路径应与服务器上 `command -v npm` 的实际结果一致。

### 4. 加载 systemd 配置

```bash
systemctl daemon-reload
```

### 5. 停止旧的 nohup 进程

```bash
pkill -f '[u]vicorn app.main:app' || true
pkill -f '[n]ode server/index.mjs' || true
```

避免旧进程占用端口。

### 6. 启动并启用开机自启

```bash
systemctl enable --now thinklab-backend.service

systemctl enable --now thinklab-frontend.service

systemctl enable --now nginx
```

至此，前后端正式交由 systemd 管理。

---

## 十二、最终部署验证

### 1. 检查后端状态

```bash
systemctl status thinklab-backend --no-pager
```

正常情况下应显示：

```text
Active: active (running)
```

### 2. 检查前端状态

```bash
systemctl status thinklab-frontend --no-pager
```

正常情况下应显示：

```text
Active: active (running)
```

### 3. 检查 Nginx 状态

```bash
systemctl status nginx --no-pager
```

正常情况下应显示：

```text
Active: active (running)
```

### 4. 检查端口

```bash
ss -lntp | grep -E ':80|:4173|:8000'
```

最终检查到：

```text
0.0.0.0:80
127.0.0.1:8000
*:4173
```

其中，前端目前监听 `*:4173`，后续建议将其调整为仅监听 `127.0.0.1`，并同步修改 Express 服务监听配置。

### 5. 检查后端 API

```bash
curl -sS -o /dev/null \
-w 'Backend HTTP %{http_code}\n' \
http://127.0.0.1:8000/openapi.json
```

实际返回：

```text
Backend HTTP 200
```

### 6. 检查前端

```bash
curl -I http://127.0.0.1:4173/
```

实际返回：

```text
HTTP/1.1 200 OK
```

### 7. 检查 Nginx 网站入口

```bash
curl -I http://127.0.0.1/
```

实际返回：

```text
HTTP/1.1 200 OK
```

说明：

- 后端 API 可以访问。
- 前端服务可以访问。
- Nginx 可以正常代理请求。
- 网站入口可以正常返回页面。

**最终验证结果：前后端服务均已运行，网站入口返回 HTTP 200，部署成功。**

---

## 十三、日常运维命令

完成 systemd 配置后，不需要再使用 nohup 手动启动服务。

### 1. 查看服务状态

```bash
systemctl status thinklab-backend

systemctl status thinklab-frontend

systemctl status nginx
```

### 2. 重启服务

重启后端：

```bash
systemctl restart thinklab-backend
```

重启前端：

```bash
systemctl restart thinklab-frontend
```

重启 Nginx：

```bash
systemctl restart nginx
```

### 3. 查看日志

查看后端最近 50 条日志：

```bash
journalctl -u thinklab-backend -n 50 --no-pager
```

查看前端最近 50 条日志：

```bash
journalctl -u thinklab-frontend -n 50 --no-pager
```

实时查看后端日志：

```bash
journalctl -u thinklab-backend -f
```

实时查看前端日志：

```bash
journalctl -u thinklab-frontend -f
```

### 4. 检查是否启用了开机自启

```bash
systemctl is-enabled thinklab-backend

systemctl is-enabled thinklab-frontend

systemctl is-enabled nginx
```

正常情况下均应返回：

```text
enabled
```

### 5. 服务异常时的处理

如果网站再次出现 502：

第一步，检查服务：

```bash
systemctl status thinklab-backend
systemctl status thinklab-frontend
systemctl status nginx
```

第二步，查看前端日志：

```bash
journalctl -u thinklab-frontend -n 50 --no-pager
```

第三步，必要时重启前端：

```bash
systemctl restart thinklab-frontend
```

如果仍然无法访问，再检查后端和 Nginx 日志。

---

## 十四、Docker 部署方案说明

本次部署过程中还使用 CodeBuddy 创建了以下 Docker 部署文件：

```text
code/
├── backend/
│   └── Dockerfile
├── frontend/
│   └── Dockerfile
├── .dockerignore
├── .env.production.example
├── docker-compose.prod.yml
└── .gitignore
```

这些文件的作用：

| 文件 | 用途 |
|---|---|
| `backend/Dockerfile` | 构建后端镜像 |
| `frontend/Dockerfile` | 构建前端镜像 |
| `.dockerignore` | 排除不需要进入镜像的文件 |
| `.env.production.example` | 生产环境变量模板 |
| `docker-compose.prod.yml` | 编排生产环境服务 |
| `.gitignore` | 忽略敏感配置及临时文件 |

**重要说明：**

这些 Docker 部署文件虽然已经创建，但本次 ECS 最终运行的前后端并没有通过 Docker Compose 启动。

当前正式运行方式仍然是：

```text
systemd
  ├── thinklab-backend
  ├── thinklab-frontend
  └── nginx
```

Docker Compose 可以作为后续标准化部署和环境迁移的方案，但需要先单独验证镜像构建、容器网络、数据库连接和 API 配置，再考虑迁移。

---

## 十五、当前部署状态与后续优化

### 1. 当前已经完成

- [x] 阿里云 ECS 创建与 Ubuntu 环境准备
- [x] Git、Python、Node.js、Docker 安装
- [x] 项目上传到 ECS
- [x] Python 虚拟环境创建
- [x] 后端依赖安装
- [x] 前端依赖安装
- [x] 前端生产构建
- [x] FastAPI 后端运行
- [x] Node.js 前端运行
- [x] SQLite 数据库运行
- [x] 本地向量存储配置
- [x] DeepSeek 环境变量配置
- [x] Nginx 反向代理配置
- [x] 公网 HTTP 访问
- [x] systemd 后端服务配置
- [x] systemd 前端服务配置
- [x] Nginx 开机自启
- [x] 前后端服务开机自启
- [x] 网站 HTTP 200 验证

### 2. 后续建议

以下工作尚不应视为已经完成：

| 优化项目 | 当前情况 | 建议 |
|---|---|---|
| HTTPS | 尚未配置 | 申请 SSL 证书并配置 HTTPS |
| PostgreSQL | 尚未启用 | 后续根据用户量和数据需求迁移 |
| SQLite 备份 | 尚未建立自动备份机制 | 定期备份数据库文件 |
| 前端监听地址 | 当前为 `*:4173` | 调整为 `127.0.0.1` |
| Docker Compose | 文件已创建，未用于当前运行 | 单独测试后再迁移 |
| 监控告警 | 尚未配置 | 增加网站可用性监测 |
| 日志管理 | 已有 systemd 日志 | 后续设置日志保留和磁盘空间管理 |

### 3. 服务器与本地电脑的关系

ECS 是独立运行的云服务器。

因此：

- 关闭本地电脑，不会关闭 ECS。
- 关闭 VS Code，不会关闭 ECS。
- 关闭浏览器或 Workbench 页面，不会停止网站。
- 只要 ECS 实例保持运行，且相关服务正常，其他用户就可以访问网站。
- 如果主动停止 ECS，网站就会停止访问。

---

## 十六、部署总结

本次 ThinkLab 部署经历了从直接上传代码、安装运行环境，到前后端分离部署、Nginx 反向代理，再到 systemd 服务管理的完整过程。

部署中主要遇到三个问题：

1. ECS 无法正常连接 GitHub，最终采用 ZIP 上传方式。
2. ECS 无法从 Docker Hub 拉取 PostgreSQL 镜像，最终使用 SQLite 完成当前阶段部署。
3. 前端进程意外停止导致 Nginx 返回 502，最终通过 systemd 配置前后端自动启动和异常重启机制。

最终，ThinkLab 已经能够通过阿里云 ECS 公网访问，后端、前端和 Nginx 均通过 HTTP 200 检查。

**本次部署的最终方案是：Ubuntu 22.04 + Python venv + FastAPI + Node.js + Nginx + SQLite + DeepSeek + systemd。**

这套方案满足当前 MVP 阶段的基本部署和运行需求，后续可以继续完善 HTTPS、数据库备份、服务监控以及 Docker Compose 部署。
