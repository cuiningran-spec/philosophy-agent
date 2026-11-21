# ThinkLab 阿里云 ECS 部署实施记录

> **项目名称：** ThinkLab — 哲学对话 AI Agent  
> **部署目标：** 将 ThinkLab 从本地 Docker 环境部署到阿里云 ECS，实现公网访问和 Demo 演示。  
> **部署模式：** Demo 演示模式  
> **记录日期：** 2026 年 11 月 21 日  
> **项目仓库：** https://github.com/cuiningran-spec/philosophy-agent

---

## 一、部署目标与总体方案

### 1.1 部署目标

将 ThinkLab 项目从本地 Docker 环境迁移到阿里云 ECS，实现以下目标：

1. 将项目部署到云服务器，摆脱本地电脑运行限制。
2. 通过公网 IP 或域名访问 ThinkLab。
3. 保持前端、后端、数据库之间的正常通信。
4. 接入 DeepSeek API，实现哲学视角生成与 AI 对话。
5. 支持项目展示、功能演示和阶段性测试。
6. 控制服务器运行时间，尽量将 Demo 阶段的云资源费用控制在 300 元以内。

### 1.2 项目技术架构

ThinkLab 采用前后端分离的部署架构，通过 Docker Compose 管理服务。

| 模块 | 技术 | 主要作用 |
|---|---|---|
| 前端 | React + Vite + TypeScript | 用户交互与页面展示 |
| BFF | Node.js + Express | 前后端请求转发、SSE 流式响应 |
| 后端 | Python + FastAPI | 核心业务逻辑和 AI 服务 |
| 数据库 | PostgreSQL 16 | 用户会话等数据存储 |
| AI 模型 | DeepSeek API | 哲学分析与对话生成 |
| 容器管理 | Docker Compose | 管理项目运行服务 |
| 云服务器 | 阿里云 ECS | 提供公网运行环境 |

说明：DeepSeek 使用外部 API 调用，不需要在 ECS 上部署本地大语言模型，也不需要 GPU。

---

## 二、阿里云 ECS 配置方案

### 2.1 服务器规格

根据项目架构、Demo 使用场景和预算，确定以下推荐配置：

| 配置项 | 选择 |
|---|---|
| 云服务商 | 阿里云 |
| 实例类型 | 经济型 e |
| CPU | 2 核 |
| 内存 | 4 GiB |
| 操作系统 | Ubuntu 22.04 LTS 64 位 |
| 系统盘 | ESSD Entry |
| 磁盘容量 | 40 GiB |
| CPU 架构 | x86 |
| 公网网络 | 分配公网 IPv4 |
| 公网带宽 | 1–3 Mbps 起步 |
| 计费方式 | 按量付费，结合可用优惠额度 |

### 2.2 配置选择原因

项目需要同时运行：

- React 前端及 Node.js BFF；
- Python FastAPI 后端；
- PostgreSQL 数据库；
- Docker 容器及相关服务。

2 核 2 GiB 虽然成本更低，但多个容器同时运行可能出现内存不足的问题。因此，选择 2 核 4 GiB 作为 Demo 阶段更稳妥的起点。

### 2.3 预算规划

根据阿里云控制台此前显示的参考价格：

- 2 核 4 GiB 经济型 e：约 0.254 元/小时；
- 页面显示的免费可用时长：约 1181 小时；
- 对应实例运行额度：约 300 元；
- 1181 小时约等于连续运行 49 天。

Demo 模式不要求服务器全年 24 小时运行，因此采用按需启动、演示结束后停止的方式控制费用。

**预算注意事项：**

1. 300 元额度并不代表服务器全年免费。
2. 云盘、公网带宽、流量、快照等资源可能独立计费。
3. 停机后部分资源仍可能产生费用。
4. 最终费用以阿里云订单页面和实际账单为准。
5. 购买前需要确认个人实名认证账号是否具备相应优惠资格。

---

## 三、本地 Docker 部署环境

### 3.1 Docker 环境

ThinkLab 已在 Windows 本地环境使用 Docker 完成容器化部署。

环境信息：

| 项目 | 版本或状态 |
|---|---|
| Docker Desktop | 4.99.0 |
| Docker Engine | 29.9.3 |
| Docker Compose | v5.7.0 |
| 后端镜像 | thinklab-api:local |
| 前端镜像 | thinklab-web:local |

### 3.2 本地服务架构与验证

Docker Compose 管理的服务包括：

| 容器 | 作用 |
|---|---|
| thinklab-api-prod | Python 后端服务 |
| thinklab-postgres-prod | PostgreSQL 数据库 |
| thinklab-web-prod | 前端及相关 Web 服务 |

本地访问地址：

- 前端：http://localhost:4173
- 后端健康检查：`/api/health`

此前本地验证结果：

- 前端页面能够正常打开，HTTP 状态码为 200；
- 后端健康检查返回正常；
- 数据库连接正常；
- DeepSeek API 配置已被后端识别；
- 已成功获取三个哲学分析视角。

健康检查中曾显示：

| 检查项 | 状态 |
|---|---|
| API | ok |
| Database | up |
| LLM Mode | deepseek |
| Model | deepseek-chat |
| Embedding Provider | local |
| Vector Store | local |

以上是本地环境的验证结果，云端部署后仍需重新确认。

### 3.3 项目仓库结构

项目公开仓库：

https://github.com/cuiningran-spec/philosophy-agent

主要目录结构：

```text
philosophy-agent/
├── docs/
├── code/
│   ├── backend/
│   ├── frontend/
│   └── core_engine/
├── tests/
└── .github/
    └── workflows/
```

项目采用 Docker Compose 组织前后端服务和数据库，云端部署将以现有项目配置为基础，不需要重新开发业务功能。

---

## 四、ECS 网络与安全组配置

### 4.1 服务器创建

进入阿里云 ECS 控制台：

https://ecs.console.aliyun.com/

按照以下配置创建实例：

1. 选择经济型 e，2 核 4 GiB。
2. 选择 Ubuntu 22.04 LTS 64 位镜像。
3. 配置 ESSD Entry 40 GiB 系统盘。
4. 分配公网 IPv4。
5. 配置公网带宽。
6. 设置登录密码或 SSH 密钥。
7. 创建或选择安全组。
8. 检查最终费用明细。
9. 提交订单并启动实例。

### 4.2 安全组配置

云服务器需要配置安全组入方向规则：

| 端口 | 协议 | 授权对象 | 用途 |
|---|---|---|---|
| 22 | TCP | 自己的公网 IP | SSH 远程连接 |
| 80 | TCP | 0.0.0.0/0 | HTTP 访问 |
| 443 | TCP | 0.0.0.0/0 | HTTPS 访问 |

以下端口不应直接开放到公网：

| 端口 | 服务 | 处理方式 |
|---|---|---|
| 5432 | PostgreSQL | 仅内部访问 |
| 8000 | FastAPI | 仅内部访问 |
| 4173 | 前端服务 | 由反向代理访问 |

---

## 五、服务器初始化与项目部署

### 5.1 通过 SSH 连接服务器

在 Windows PowerShell 中执行：

```powershell
ssh root@服务器公网IP
```

首次连接时确认主机指纹，然后按照所选认证方式完成登录。连接成功后，终端将进入 Ubuntu 服务器环境。

### 5.2 初始化服务器环境

更新系统软件包：

```bash
sudo apt update
sudo apt upgrade -y
```

安装 Git：

```bash
sudo apt install git -y
```

安装 Docker：

```bash
curl -fsSL https://get.docker.com | sudo sh
```

启动 Docker：

```bash
sudo systemctl enable docker
sudo systemctl start docker
```

检查 Docker：

```bash
docker --version
```

检查 Docker Compose：

```bash
docker compose version
```

### 5.3 拉取 ThinkLab 项目代码

在服务器中执行：

```bash
git clone https://github.com/cuiningran-spec/philosophy-agent.git
```

进入项目目录：

```bash
cd philosophy-agent
```

查看项目文件：

```bash
ls -la
```

根据仓库实际 Docker Compose 配置和目录结构，确定生产部署文件的位置和启动命令。

---

## 六、生产环境配置

### 6.1 配置生产环境变量

需要在 ECS 上配置生产环境变量，主要包括：

| 配置项 | 用途 |
|---|---|
| DEEPSEEK_API_KEY | DeepSeek API 身份认证 |
| DeepSeek 模型配置 | 指定使用的模型 |
| DATABASE_URL | PostgreSQL 数据库连接 |
| PostgreSQL 密码 | 数据库身份认证 |
| CORS 配置 | 限制允许访问后端的来源 |
| 前端 API 地址 | 指向生产环境 API 或代理路径 |
| 其他项目变量 | 根据项目配置文件确定 |

具体变量名称和格式必须以项目现有 `.env.production.example`、Docker Compose 文件及后端配置为准。

### 6.2 环境变量安全要求

1. API Key 只保存在服务器环境变量或受保护的环境文件中。
2. 不将真实密钥提交到 GitHub。
3. 不在前端代码中写入 API Key。
4. 不将 PostgreSQL 密码暴露给公网。
5. 不把 `.env.production` 文件上传到公开仓库。
6. 不在聊天中发送密码、私钥和 API Key。

### 6.3 Docker Compose 生产部署配置

本地部署使用的 Docker Compose 配置需要结合云端部署环境进行调整：

1. 确保 PostgreSQL 仅供 Docker 内部网络访问。
2. 确保 FastAPI 不直接暴露公网端口。
3. 配置前端与 BFF 的生产环境请求地址。
4. 确认 SSE 流式响应能够正常工作。
5. 配置持久化数据库卷。
6. 确认后端环境变量能够正确读取。
7. 配置容器重启策略。
8. 处理本地向量存储目录的写入权限问题。

特别注意：

此前本地健康检查显示：

```text
embedding_provider=local
vectorstore=local
```

这说明当时使用的是本地向量存储，不能因为配置了 Pinecone API Key 就认定已经启用 Pinecone。云端是否使用 Pinecone，需要依据项目实际支持的配置和运行状态确定。

---

## 七、Docker 服务构建与启动

在项目根目录执行实际生产 Compose 文件对应的构建命令，例如：

```bash
docker compose -f docker-compose.prod.yml build
```

具体文件名需要以仓库实际配置为准。

构建完成后启动：

```bash
docker compose -f docker-compose.prod.yml up -d
```

查看运行状态：

```bash
docker compose ps
```

查看服务日志：

```bash
docker compose logs -f
```

如果项目使用的生产 Compose 文件名称不同，需要替换为实际文件名。

需要确认以下服务均能正常运行：

- 前端容器；
- BFF 服务；
- FastAPI 后端；
- PostgreSQL 数据库。

---

## 八、Nginx 反向代理与公网访问

### 8.1 配置 Nginx 反向代理

为了让用户通过公网 IP 或域名访问，需要配置 Nginx。

Nginx 主要负责：

1. 接收公网 HTTP/HTTPS 请求。
2. 将页面请求转发给前端。
3. 将 API 请求转发给对应服务。
4. 支持 SSE 流式响应。
5. 提供统一的公网访问入口。

预期部署架构：

```text
用户浏览器
     |
     v
公网 IP / 域名
     |
     v
Nginx 反向代理
     |
     +------> React 前端
     |
     +------> Node.js BFF
                    |
                    v
               FastAPI 后端
                    |
                    +------> PostgreSQL
                    |
                    +------> DeepSeek API
```

### 8.2 域名与 HTTPS 配置

Demo 初期可以先通过公网 IP 进行部署验证。如果需要长期展示或正式对外开放，建议配置域名和 HTTPS。

操作内容：

1. 准备域名。
2. 配置 DNS 解析，将域名指向 ECS 公网 IP。
3. 根据域名和服务器使用情况完成 ICP 备案等必要手续。
4. 申请 SSL 证书。
5. 配置 Nginx HTTPS。
6. 验证 HTTPS 访问。

---

## 九、云端功能验证

云端部署完成后，需要重点确认以下功能：

| 测试项目 | 验证内容 |
|---|---|
| 页面访问 | 浏览器能否正常打开 ThinkLab |
| API 健康检查 | 后端能否正常响应 |
| 数据库连接 | PostgreSQL 是否正常 |
| AI 请求 | DeepSeek API 是否能够正常调用 |
| 哲学视角生成 | 能否正常返回三个哲学视角 |
| 继续探索 | 用户选择视角后能否继续对话 |
| SSE 流式响应 | AI 回复是否能够正常流式输出 |
| 会话功能 | 会话创建和数据保存是否正常 |
| 异常处理 | API 失败时是否有明确提示 |
| 公网访问 | 非本机网络是否能够正常访问 |

重点验证项目的核心 MVP 流程：

```text
用户输入现实问题
        |
        v
AI 分析用户问题
        |
        v
生成三个哲学视角
        |
        v
用户选择其中一个视角
        |
        v
继续针对性探索
        |
        v
整理本次思考结果
```

---

## 十、Demo 运行与费用管理

由于采用 Demo 演示模式，服务器不需要全年运行。

建议：

1. 演示前提前启动 ECS。
2. 确认 Docker 容器全部正常。
3. 演示结束后根据实际需求停止实例。
4. 关注按量付费账单。
5. 重要演示前备份数据库。
6. 保留项目代码和生产配置的安全副本。
7. 不需要时及时释放不再使用的资源。

注意：停止实例不代表所有云资源都停止计费，应确认停机模式、云盘和公网 IP 的计费规则。

---

## 十一、最终部署目标与执行流程

完成全部部署工作后，ThinkLab 将具备以下运行能力：

- 通过阿里云 ECS 提供云端运行环境；
- 通过公网 IP 或域名访问前端；
- 使用 Docker Compose 管理前后端和数据库；
- 通过 DeepSeek API 提供哲学分析与对话能力；
- 支持用户输入现实问题、生成三个哲学视角、选择视角并继续探索；
- 支持阶段性 Demo 展示；
- 通过按需启动和停止控制云服务器运行成本。

整体部署按照以下顺序推进：

1. 完成阿里云 ECS 购买与安全组配置。
2. 获取公网 IP，通过 SSH 连接服务器。
3. 安装 Docker、Docker Compose 和 Git。
4. 克隆 GitHub 仓库。
5. 配置生产环境变量。
6. 调整 Docker Compose 生产配置。
7. 构建并启动 Docker 服务。
8. 配置 Nginx 和公网访问。
9. 根据需要配置域名和 HTTPS。
10. 验证 ThinkLab 核心功能。
11. 完成 Demo 演示准备和费用管理。

**最终目标：让 ThinkLab 从本地可运行的项目，转变为能够通过公网访问、完整展示核心功能的云端 AI 应用。**
