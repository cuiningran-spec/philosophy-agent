---
theme: default
title: ThinkLab · 知识库检索智能体 答辩
class: text-center
highlighter: shiki
lineNumbers: false
transition: slide-left
mdc: true
---

# ThinkLab

## 哲学知识库检索智能体

**帮助用户从多个哲学视角理解现实问题，形成个人思考的 AI Agent**

日期：2026 年 11 月 28 日

---

# 目录

<br/>

## 1. 产品设计

<br/>

## 2. 产品设计应用的原则

<br/>

## 3. 产品实现

---

# 1. 产品设计

## 1.1 产品使命、口号和策略

- **1.1.1 使命**：打破单一思维的局限，帮助用户从多个哲学视角审视现实问题，最终形成属于个人的独立见解。
- **1.1.2 口号**：“多一种视角，多一种可能。”
- **1.1.3 目标用户**：面临人生困惑的青年群体、对哲学思辨感兴趣的爱好者、需要思维启发的创作者。
- **1.1.4 如何获得用户**：通过高质量哲学社群推广、社交媒体“现实问题+哲学视角”内容引流。
- **1.1.5 团队优势**：具备全栈开发能力（React + Node.js + FastAPI），深入理解 LangChain 编排机制，且拥有丰富的人文知识积累。

---

# 1. 产品设计

## 1.1.6 如何做到差异化

| 维度 | 通用大模型 (如 ChatGPT) | 传统问答社区 | 我们的“ThinkLab 智能体” |
|---|---|---|---|
| **回答方式** | 单一生成 | 人类主观碎片化回答 | **生成 3 种截然不同的哲学视角供选择** |
| **深度体验** | 缺乏追问空间 | 难以进行深度多轮对话 | 选择视角后，基于 RAG 知识库进行**深度多轮追问** |
| **最终产出** | 没有沉淀 | 页面冗长难以阅读 | **一键生成结构化思考总结（洞见/张力/实践）** |

---

# 1. 产品设计

## 1.2 产品定义与用户故事

### 产品定义：
- **对于**（面临现实困惑的用户）
- **他们**（苦于大模型回答过于同质化，缺乏多元视角）
- **产品/项目** 是一个（多视角哲学探索智能体）
- **它能够**（针对用户的现实问题，生成三种不同的哲学视角，并引导用户持续追问，最终生成思考总结）
- **不同于**（传统的聊天机器人）
- **我们的产品**（强调“探索”与“沉淀”，通过 RAG 知识库确保回答的哲学严谨性）。

## 用户故事
> 作为一个“**面临职业焦虑的青年**”，我想要“**看看斯多葛主义和存在主义会怎么看待我现在的处境**”，以便于“**我能跳出单一的情绪，形成自己的解决思路**”。

---

# 2. 产品设计应用的原则

本项目在设计中遵循了以下几条原则：

- **需求原则**：一切从用户“需要多视角启发”这个真实痛点出发，没有为了做而做，产品功能直接对应需求。
- **创新原则**：把“生成三个不同视角”和“进行结构化总结”作为核心差异点，让用户能真正看到不同哲学流派如何解读同一个问题。
- **收敛原则**：用提示词锁定当前流派，禁止模型跨流派漂移。（用户选了斯多葛，AI 就只从斯多葛的角度回应，不会突然切换到道家思想）
- **降级可用原则**：考虑到演示和部署环境的不确定性，做了多级降级，保证任何情况下系统都能跑起来。

---

# 3. 产品实现

## 3.1 用户体验设计因素
- **交互简洁**：对话式 UI，纸质/墨色的视觉风格，契合哲学思辨的沉静感。
- **可解释性**：界面直接展示检索出处（“这一步借用了知识库中的...”），提升可信度。
- **流式响应**：后端支持 SSE，前端边打边出，极大降低用户等待焦虑。

---

## 3.2 编程语言及框架选型

| 条目名称 | 条目内容 | 选型原因 |
|---|---|---|
| **Agent 编排** | LangChain | 统一 Prompt / LLM / Parser 链式调用。 |
| **LLM 模型** | DeepSeek-Flash | 兼容 OpenAI 协议，成本低，中文能力强。 |
| **向量数据库** | Pinecone | Serverless 索引自动创建，检索性能优异。 |
| **API 框架** | FastAPI | 异步支持极好，自动生成 Swagger 文档。 |
| **持久化** | PostgreSQL | 支持 JSONB，完美适配结构化总结的存储。 |
| **前端/服务** | React + Node.js | Vite 极速打包，Node 作为 BFF 层反向代理支持 SSE 透传。 |

---

# 3. 产品实现

## 3.3 代码仓库与生命周期管理
- **仓库链接**：https://github.com/cuiningran-spec/philosophy-agent

<div style="display: flex; justify-content: space-around; margin-top: 30px; align-items: center;">
  <div style="text-align: center;">
    <img src="/1.png" style="height: 260px; border-radius: 8px;" alt="提交历史" />
    <p style="margin-top: 10px;">Git 提交历史</p>
  </div>
  <div style="text-align: center;">
    <img src="/2.png" style="height: 260px; border-radius: 8px;" alt="项目看板" />
    <p style="margin-top: 10px;">Team Planning 看板</p>
  </div>
</div>

---

## 3.4 生命周期遇到的问题及解决

| 问题类别 | 问题名称 | 解决办法 |
|---|---|---|
| 分析阶段 | 多流派概念混淆 | 在系统提示词中锁定当前视角，禁止模型跨流派闲聊。 |
| 分析阶段 | 三视角区分度不足 | 在 Prompt 中显式定义每个视角的“核心追问”与“典型哲学家”，强制拉开差异。 |
| 开发阶段 | 长对话导致 Token 爆炸 | 引入多轮记忆机制，超过 8 轮自动压缩为“滚动摘要”。 |
| 测试阶段 | 模型输出不可控（护栏缺失） | 构建双层护栏：Prompt 层锁定流派；代码层拦截异常，失败时自动降级模板模型。 |
| 部署阶段 | 服务意外停止、重启后无法访问 | 将前后端交由 Ubuntu `systemd` 托管，配置开机自启与进程守护，彻底解决 ECS 重启宕机问题。 |

---

# 3. 产品实现

## 3.5.1 软件概要设计：系统架构图

```mermaid {scale: 0.6}
%%{init: {'theme': 'dark'}}%%
flowchart LR
    subgraph 前端
        U[用户] --> React[React 18 + Vite]
    end
    
    subgraph 业务逻辑
        React -->|SSE| Node[Node.js BFF 反代]
        Node -->|REST/SSE| FastAPI[FastAPI 服务]
        FastAPI --> Engine[LangChain 内核]
    end
    
    subgraph 数据存储
        Engine -.-> PC[(PineCone向量库)]
        Engine -.-> PG[(PostgreSQL)]
    end
```

---

## 3.5.2 基础设施与部署架构图

```mermaid {theme: 'dark', scale: 0.68}
flowchart LR
    User((用户浏览器)) -->|HTTPS| Nginx[Nginx / 静态资源托管]
    Nginx -->|SSE 流式请求| Node[Node.js BFF 反代]
    Node -->|REST API| FastAPI[FastAPI 业务后端]

    FastAPI -.->|读写数据| PG[(PostgreSQL 数据库)]
    FastAPI -.->|向量检索| Pinecone[(PineCone向量库)]
    FastAPI -.->|API 调用| DeepSeek[DeepSeek 大模型接口]
```

---

## 3.5.3 智能体技术设计：Agent 基本组成

<div style="font-size: 13px; line-height: 1.2; margin-top: 5px;">

本项目采用经典的 Agent 架构，通过 LangChain 编排，各核心组件分工如下：

| 核心组件 | 在本项目中的具体实现 | 发挥的作用 | 对应文件 |
| :--- | :--- | :--- | :--- |
| **大脑 (LLM)** | DeepSeek-Flash (OpenAI 兼容协议) | 负责逻辑推理、文本生成、多视角角色扮演。 | `core_engine/thinklab_core/llm.py` |
| **规划 (Planning)** | LangChain 链式调用（视角/对话/总结链） | 将复杂的探索任务拆解为“生成视角 -> 多轮对话 -> 结构化总结”的 SOP 流程。 | `core_engine/thinklab_core/chains.py` |
| **记忆 (Memory)** | 窗口记忆 + 滚动摘要压缩 (PostgreSQL) | 记住多轮对话上下文，长对话自动压缩摘要，防止 Token 爆炸并保持人设不崩。 | `core_engine/thinklab_core/memory.py` |
| **工具与知识库** | RAG 检索 (Pinecone 向量库 + 加权重排) | 提供外挂知识库，按用户选择的哲学流派加权召回语料，确保回答不串味且有据可查。 | `core_engine/thinklab_core/vectorstore.py` |
| **护栏** | 降级兜底机制 & 视角锁定 | 在模型 API 失败时自动降级模板模型；提示词锁定当前流派，禁止跨流派漂移。 | `core_engine/thinklab_core/config.py` + `prompts.py` |

</div>

> **架构亮点**：通过 LLM 的推理能力结合 RAG 的外部知识，配合多轮记忆机制，实现了真正“懂哲学、能追问、有记忆”的智能体。

---

## 3.5.4 数据库设计：E-R 图

<div style="display: flex; justify-content: space-between; align-items: flex-start; margin-top: 10px;">
  
  <!-- 左侧：E-R 图 (注意 mermaid 前不要留空格) -->
  <div style="width: 55%;">

```mermaid {scale: 0.55}
%%{init: {'theme': 'dark'}}%%
erDiagram
    SESSIONS ||--o{ MESSAGES : contains
    SESSIONS ||--o{ PERSPECTIVES : generates
    SESSIONS ||--o{ SUMMARIES : produces
    SESSIONS {
        int id PK
        string question
        string lens
        string rolling_summary
        string status
    }
    MESSAGES {
        int id PK
        int session_id FK
        string role
        string content
        int turn_index
        json sources
    }
    PERSPECTIVES {
        int id PK
        int session_id FK
        string key
        string name
        string headline
        string thinker
    }
    SUMMARIES {
        int id PK
        int session_id FK
        int version
        json insights
        json tensions
        json practices
    }
```

  </div>

  <!-- 右侧：文字说明 -->
  <div style="width: 42%; font-size: 14px; line-height: 1.6; margin-top: 20px;">
    <strong>核心表关系说明：</strong><br/><br/>
    • <strong>SESSIONS (会话)</strong>：主表，记录用户一次探索（问题、视角、滚动摘要）。<br/><br/>
    • <strong>MESSAGES (对话)</strong>：对话流水，<code>sources</code> 字段用 JSONB 保存引用来源。<br/><br/>
    • <strong>PERSPECTIVES (视角)</strong>：保存该次会话生成的三种哲学视角。<br/><br/>
    • <strong>SUMMARIES (总结)</strong>：支持版本递增，生成后仍可继续对话。
  </div>

</div>

---

## 3.5.5 接口设计
对外暴露三个核心接口：

| 接口名称 | 功能 | 特点 |
|---|---|---|
| `POST /api/sessions` | 创建会话生成视角 | 并发调用大模型与向量库 |
| `POST /api/sessions/{id}/messages/stream` | 流式对话 | **SSE（Server-Sent Events）** 实时推送 |
| `POST /api/sessions/{id}/summaries` | 生成思考总结 | 输出洞见、张力、实践等结构化 JSON |

---

## 3.6.1 质量控制：全链路日志与降级

<div style="display: flex; justify-content: space-between; align-items: flex-start; margin-top: 20px;">
  <div style="width: 48%; text-align: center;">
    <img src="/error1.png" style="height: 300px; border-radius: 8px;" />
    <p style="margin-top: 10px; font-size: 14px;">全链路日志配置，支持文件写入</p>
  </div>
  <div style="width: 48%; text-align: center;">
    <img src="/error2.png" style="height: 300px; border-radius: 8px;" />
    <p style="margin-top: 10px; font-size: 14px;">异常兜底：DeepSeek 失败降级模板模型</p>
  </div>
</div>

> **零密钥体验**：即使没有任何 API Key 和数据库，通过 SQLite 降级和本地哈希向量降级，系统仍能完整跑通 MVP。

---

## 3.6.2 质量工具：Pylint 扫描与复杂度

<div style="display: flex; justify-content: space-around; margin-top: 20px;">
  <div style="text-align: center;">
    <img src="/pylint.png" style="height: 250px; border-radius: 8px;" />
    <p style="margin-top: 10px;">Pylint 规范扫描：0 阻断性错误</p>
  </div>
  <div style="text-align: center;">
    <img src="/圈复杂度.png" style="height: 250px; border-radius: 8px;" />
    <p style="margin-top: 10px;">所有函数圈复杂度低，通过检测</p>
  </div>
</div>

---

## 3.7 代码统计：全栈模块划分

<img src="/代码1.png" style="display: block; margin: 0 auto; height: 300px; border-radius: 8px;" />

- **模块划分**：`core_engine`（AI 内核）、`backend`（FastAPI 后端）、`frontend`（React 前端）。
- **AI 辅助生成 (80%)**：UI 组件、样板 CRUD 代码。
- **团队手写 (20%)**：RAG 重排逻辑、多轮记忆压缩、异常降级兜底机制。

---

# 附录：相关开源代码与文献来源

1. **Slidev 幻灯片框架**: https://github.com/slidevjs/slidev
2. **LangChain 智能体框架**: https://github.com/langchain-ai/langchain
3. **Pinecone 向量数据库**: https://www.pinecone.io/
4. **DeepSeek API 文档**: https://platform.deepseek.com/
5. **FastAPI 官方文档**: https://fastapi.tiangolo.com/

---

# 第二部分：展示作品功能 

https://cuiningran-spec.github.io/philosophy-agent/1

**在本机运行作品，展示核心功能逻辑：**

1. **多视角生成**：输入现实问题（如“我最近很焦虑”），展示生成的三种哲学视角（斯多葛、存在主义、道家）。
2. **知识库溯源**：选择其中一个视角，提问并展示回答底部引用的「知识库出处」。
3. **多轮记忆验证**：追问几个问题后，问“我最开始问你的问题是什么”，验证记忆窗口。
4. **结构化总结**：点击生成总结，展示包含“洞见、张力、实践”的结构化卡片。

---

# 第三部分：回答评委问题 

## 感谢聆听，欢迎提问！
