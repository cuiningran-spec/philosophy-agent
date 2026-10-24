# ThinkLab · 知识库检索智能体

> 帮助用户从多个哲学视角理解现实问题，并通过自主选择探索方向，形成个人思考的哲学 AI Agent。
> 本目录为 MVP 的 Web 应用代码：**LangChain + Pinecone（检索智能体内核）+ FastAPI + PostgreSQL + React + Node.js**。

---

## 1. 产品流程与代码映射

| MVP 步骤 | 用户动作 | 前端页面 | 后端接口 | 内核能力 |
| --- | --- | --- | --- | --- |
| 01 提问 | 输入一个现实问题 | `HomePage`（`/`） | `POST /api/sessions` | 读题 + 知识库检索 |
| 02 三视角 | Agent 给出三种有区别的哲学视角 | `PerspectivesPage`（`/perspectives/:id`） | 同上（返回 3 个 lens） | `generate_perspectives()`（RAG + 结构化输出） |
| 03 多轮对话 | 选择一个视角并持续追问 | `DialoguePage`（`/dialogue/:id`） | `POST /api/sessions/{id}/lens`、`/messages`、`/messages/stream` | 检索增强生成 + **多轮记忆（窗口 + 滚动摘要）** |
| 04 思考总结 | 随时点击「生成思考总结」 | `SummaryPage`（`/summary/:id`） | `POST /api/sessions/{id}/summaries` | `generate_summary()` → 洞见 / 张力 / 实践 |
| 附加 | 知识库 FAQ 问答 | `FaqPage`（`/faq`） | `POST /api/faq/ask`、`GET /api/kb/search` | `answer_faq()` |
| 附加 | 回看历史探索 | `RecordsPage`（`/records`） | `GET /api/sessions` | — |

生成总结**不会结束对话**：记录按 `version` 递增保存，界面提示「记录已形成，仍可继续 / 记录可更新」，用户可继续追问并再次生成。

---

## 2. 目录结构

```
code/
├── core_engine/                 # Python：LangChain + Pinecone 检索智能体内核
│   ├── requirements.txt
│   └── thinklab_core/
│       ├── config.py            # 全部配置（环境变量，缺失密钥自动降级）
│       ├── schemas.py           # 内核数据结构
│       ├── lenses.py            # 三种哲学视角画像与模板话术
│       ├── embeddings.py        # OpenAIEmbeddings / 本地哈希向量（降级，独立于 LLM）
│       ├── vectorstore.py       # Pinecone / 本地 JSON 向量库（降级）
│       ├── llm.py               # DeepSeek（OpenAI 兼容协议）/ OpenAI 备用 / 模板化 LLM（降级）
│       ├── prompts.py           # LangChain ChatPromptTemplate
│       ├── memory.py            # 多轮记忆：窗口记忆 + 滚动摘要压缩
│       ├── chains.py            # RAG 链：视角 / 对话 / 总结 / FAQ / 检索 / 灌库
│       ├── service.py           # ThinkLabAgent 门面（对外唯一入口）
│       ├── ingest.py            # 灌库 CLI
│       └── knowledge/           # 种子语料（34 条概念/原典/练习）+ 12 条 FAQ
├── backend/                     # Python：FastAPI 服务（HTTP API + PostgreSQL）
│   ├── requirements.txt
│   ├── schema.sql               # PostgreSQL 建表脚本（参考）
│   └── app/
│       ├── main.py              # 应用装配、CORS、启动建表与知识库预热
│       ├── config.py / db.py    # 配置与 SQLAlchemy（PostgreSQL，可降级 SQLite）
│       ├── models.py            # ORM 模型（7 张表）
│       ├── repositories.py      # 数据访问层
│       ├── serializers.py       # ORM → Pydantic
│       ├── deps.py              # 依赖注入
│       └── routers/             # sessions / chat / summaries / knowledge / health
├── frontend/                    # React + Vite + TypeScript 聊天界面
│   ├── server/index.mjs         # Node.js BFF：静态托管 + /api 反代（支持 SSE 透传）
│   └── src/
│       ├── api.ts               # REST 客户端 + SSE 解析
│       ├── pages/               # Home / Perspectives / Dialogue / Summary / FAQ / Records
│       ├── components/          # Header / LensCard / MessageBubble / Composer / Steps / Icon
│       └── styles.css           # 纸质哲学风格设计系统（与原型一致）
├── docker-compose.yml           # PostgreSQL 16
└── .env.example                 # 全部环境变量
```

---

## 3. 技术选型说明

| 关注点 | 选型 | 说明 |
| --- | --- | --- |
| Agent 编排 | **LangChain**（`ChatPromptTemplate` / `Runnable` / `PydanticOutputParser` / Memory） | 视角、对话、总结、FAQ 四条链统一为 `prompt \| llm \| parser` |
| 向量检索 | **Pinecone**（`langchain-pinecone`，Serverless 索引自动创建） | 未配置 `PINECONE_API_KEY` 时降级为本地 JSON 向量库，接口保持一致 |
| Embedding | OpenAI `text-embedding-3-small` | DeepSeek 不提供 embedding 接口，向量化独立配置；无密钥时使用确定性哈希向量 |
| LLM | **DeepSeek** `deepseek-chat`（`ChatOpenAI` 指向 `https://api.deepseek.com`，OpenAI 兼容协议） | 无密钥时使用 `TemplateChatModel`（合法 `BaseChatModel`），保证零密钥可演示 |
| API | **FastAPI** | REST + SSE 流式对话（`/messages/stream`） |
| 持久化 | **PostgreSQL**（SQLAlchemy 2.0 + psycopg2） | `THINKLAB_DB_MODE=auto` 在连不上 PG 时降级 SQLite，便于本地一键演示 |
| 前端 | **React 18 + Vite + TypeScript** | 手写 CSS 复刻原型（纸张/墨色/衬线）设计系统 |
| Web 服务 | **Node.js（Express）** | 托管 `dist/`，并把 `/api` 反代到 FastAPI（含 SSE 流式透传） |

---

## 4. 数据库结构（PostgreSQL）

| 表 | 作用 | 关键字段 |
| --- | --- | --- |
| `sessions` | 一次探索 | `question`、`lens`、`lens_name`、`core_ask`、**`rolling_summary`（长对话滚动摘要）**、`status` |
| `perspectives` | 该问题下的三种视角 | `key/name/en/core_ask/headline/quote/thinker/fit_for/opening/retrieved` |
| `messages` | 对话流水 | `role`、`content`、`turn_index`、`seq`、`sources(JSONB)` |
| `summaries` | 结构化思考记录 | `version`、`insights/tensions/practices/keywords/excerpts/sources(JSONB)` |
| `knowledge_docs` | 知识库文档审计 | `doc_id`、`school`、`thinker`、`kind`、`content` |
| `faq_entries` | FAQ 条目 | `faq_id`、`question`、`answer`、`school` |
| `retrieval_logs` | 检索审计 | `query`、`school`、`hits(JSONB)`（可解释性/效果评估） |

> JSONB 用于存放检索出处与结构化总结，兼顾灵活性与可查询性；`messages.sources` 让界面可以展示「这句话借用了哪条语料」。

---

## 5. 快速开始

### 5.0 前置条件

- Python 3.10+（推荐 3.12）
- Node.js 18+
- PostgreSQL 14+（可用 `docker compose up -d` 启动）

### 5.1 一键起数据库

```bash
cd code
docker compose up -d            # PostgreSQL: localhost:5432 / thinklab
```

### 5.2 启动智能体服务（FastAPI）

```bash
cd code
python3 -m venv .venv && ./.venv/bin/pip install -r core_engine/requirements.txt -r backend/requirements.txt

cd backend
PYTHONPATH=. ../.venv/bin/python -m uvicorn app.main:app --reload --port 8000
# Swagger: http://localhost:8000/docs   健康检查: http://localhost:8000/api/health
```

启动时会自动：建表 → 灌入内置哲学语料（幂等）。也可手动灌库：

```bash
cd core_engine && ../.venv/bin/python -m thinklab_core.ingest --rebuild --query "焦虑"
```

### 5.3 启动 Web（开发模式）

```bash
cd frontend
npm install
npm run dev          # http://localhost:5173（Vite 已代理 /api → 8000）
```

### 5.4 生产模式（React + Node.js）

```bash
cd frontend
npm run build        # 类型检查 + 打包到 dist/
npm run server       # Node.js 服务：http://localhost:4173
```

Node 服务通过 `AGENT_API_BASE`（默认 `http://127.0.0.1:8000`）连接 FastAPI，`PORT` 可改端口。

### 5.5 零密钥体验

不配置任何密钥即可完整走通 MVP（LLM 走模板模型、向量库走本地索引、数据库可降级 SQLite）。

接入真实模型只需两步：

```bash
export DEEPSEEK_API_KEY=sk-xxxx        # 对话生成（DeepSeek）
export OPENAI_API_KEY=sk-yyyy          # 可选：向量化（DeepSeek 不提供 embedding）
```

重启服务后 `/api/health` 的 `llm_mode` 会变为 `deepseek`；配置 `PINECONE_API_KEY` 后自动切换为 Pinecone 向量库。

---

## 6. 环境变量

复制 `code/.env.example` 为 `.env`（或在运行目录导出同名变量）：

| 变量 | 默认 | 说明 |
| --- | --- | --- |
| `DEEPSEEK_API_KEY` | 空 | **主用 LLM 密钥**，为空时 LLM 降级为模板模型 |
| `DEEPSEEK_BASE_URL` | `https://api.deepseek.com` | OpenAI 兼容地址 |
| `DEEPSEEK_MODEL` | `deepseek-chat` | `deepseek-chat` / `deepseek-reasoner` |
| `DEEPSEEK_TEMPERATURE` | `0.65` | 生成温度 |
| `DEEPSEEK_MAX_TOKENS` | 空 | 可选，单轮最大 token |
| `OPENAI_API_KEY` | 空 | 向量化（embedding）密钥；仅在 `THINKLAB_LLM_MODE=openai` 时兼作备用 LLM |
| `OPENAI_MODEL` | `gpt-4o-mini` | 备用对话模型（LLM 走 OpenAI 时生效） |
| `OPENAI_EMBEDDING_MODEL` | `text-embedding-3-small` | 向量模型 |
| `PINECONE_API_KEY` | 空 | 为空时向量库降级为本地索引 |
| `PINECONE_INDEX` | `thinklab-philosophy` | 索引名（不存在时自动创建 Serverless 索引） |
| `DATABASE_URL` | 由 `POSTGRES_*` 拼接 | PostgreSQL 连接串 |
| `THINKLAB_DB_MODE` | `auto` | `auto / postgres / sqlite` |
| `THINKLAB_LLM_MODE` | `auto` | `auto / deepseek / openai / template` |
| `THINKLAB_LLM_FALLBACK` | `true` | DeepSeek 调用失败时用模板模型兜底，避免对话中断（设为 `false` 则直接报错） |
| `THINKLAB_VECTORSTORE_MODE` | `auto` | `auto / pinecone / local` |
| `THINKLAB_RETRIEVAL_TOP_K` | `4` | 每次召回条数 |
| `THINKLAB_MEMORY_WINDOW_TURNS` | `6` | 进入提示词的近期轮次 |
| `THINKLAB_MEMORY_COMPRESS_TURNS` | `8` | 超过该轮次触发滚动摘要压缩 |
| `AGENT_API_BASE` / `PORT` | `http://127.0.0.1:8000` / `4173` | Node.js Web 服务反代目标与端口 |

---

## 7. API 一览（前缀 `/api`）

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/health` | 服务与运行时信息（LLM 模式、向量库、数据库连通性） |
| POST | `/sessions` | 提交问题 → 返回会话 + **三种哲学视角** |
| GET | `/sessions` | 历史探索列表 |
| GET | `/sessions/{id}` | 会话详情（视角 + 消息 + 最新记录） |
| GET | `/sessions/{id}/lenses` | 该会话的三种视角 |
| POST | `/sessions/{id}/lens` | 选择视角（写入会话并生成开场语，可保留/清空历史） |
| POST | `/sessions/{id}/messages` | 发送追问（检索 + 记忆 → 回复，含出处） |
| POST | `/sessions/{id}/messages/stream` | **SSE 流式**对话：`user → token* → done` |
| POST | `/sessions/{id}/summaries` | 生成结构化思考记录（version 递增，对话不结束） |
| GET | `/sessions/{id}/summaries` | 该会话的所有版本记录 |
| GET | `/summaries/{id}` | 记录详情 |
| POST | `/faq/ask` | FAQ 问答（先检索再生成，返回命中条目与出处） |
| GET | `/faq` | FAQ 条目列表 |
| GET | `/kb/search?q=&school=&k=` | 知识库语义检索（可解释性展示） |
| POST | `/kb/ingest?rebuild=false` | 灌库（向量库 + PostgreSQL 同步） |
| GET | `/kb/docs` | 知识库文档列表 |
| GET | `/lenses` | 三种视角画像（配色、核心追问、推荐追问） |

**SSE 事件格式**

```
event: user
data: {"message": {...}}

event: token
data: {"content": "……"}

event: done
data: {"message": {...}, "sources": [...]}
```

---

## 8. 智能体内核设计要点

1. **检索增强（RAG）**：`retrieve()` 先取候选 `top_k*3` 条，再按当前流派加权（`+0.18` 同流派、`+0.06` 通用条目）重排，保证「选了斯多葛就主要召回斯多葛语料」；命中结果写入 `messages.sources` 与 `retrieval_logs`，界面可直接看到出处。
2. **多轮记忆**：`DialogueMemory` 用 `ConversationBufferWindowMemory` 保留近期轮次；当用户轮次超过阈值时，用 `ConversationSummaryMemory` 把早期对话压缩为滚动摘要，落库到 `sessions.rolling_summary`，实现长对话不丢上下文、也不无限膨胀。
3. **结构化输出**：视角与总结使用 `PydanticOutputParser` 约束 JSON（`PerspectivesGeneration` / `SummaryGeneration`），解析失败时自动回退到模板内容，保证接口可用性。
4. **视角一致性**：对话系统提示词固定「当前视角 + 核心追问」，禁止跨流派漂移与心理诊断，回复结尾回抛一个可继续回答的小问题。
5. **降级可运行**：`auto` 模式下自动检测密钥与数据库连通性，依次降级 LLM / 向量库 / 数据库，任何环境都能启动演示。
6. **LLM 失败兜底**：DeepSeek 调用失败（网络 / 鉴权 / 限流）时自动改用内置模板模型继续输出，并在日志打印原因；设置 `THINKLAB_LLM_FALLBACK=false` 可关闭兜底、直接暴露错误。

---

## 9. 常见问题

- **为什么回答里有「（这一步借用了知识库中的…）」？** 这是检索出处的显式呈现，便于用户追溯来源；可在内核 `chains.py` 中关闭。
- **如何扩展知识库？** 在 `core_engine/thinklab_core/knowledge/seed_docs.py` 追加语料后调用 `POST /api/kb/ingest?rebuild=true`，或直接将文档写入 `knowledge_docs` 表并灌入向量库。
- **如何接入 DeepSeek？** 设置 `DEEPSEEK_API_KEY`（可选 `DEEPSEEK_BASE_URL` / `DEEPSEEK_MODEL`），重启服务即可，`/api/health` 中 `llm_mode` 变为 `deepseek`、`llm_model` 显示 `deepseek-chat`。DeepSeek 与 OpenAI 协议兼容，因此复用 `langchain-openai` 的 `ChatOpenAI` 并指向 `https://api.deepseek.com`，无需额外 SDK。
- **为什么还要 OpenAI 的 key？** 只为了 embedding：DeepSeek 目前不提供向量化接口。若只配置 `DEEPSEEK_API_KEY`，向量化会自动降级为本地哈希向量（功能完整、召回精度略低）；也可把 `OPENAI_BASE_URL` 指向任何 OpenAI 兼容的 embedding 网关。
- **如何验证模型是否真的被调用？** `GET /api/health` 查看 `agent.llm_mode` / `agent.llm_model`；`GET /api/kb/search?q=焦虑` 查看召回语料。
