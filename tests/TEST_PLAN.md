# ThinkLab 自动化测试文档（TEST_PLAN）

> 本文档为测试总纲与用例登记簿，由组员 A 维护结构，B / C / D 负责填写各自的测试用例与执行结果。
> **禁止伪造执行状态与覆盖率数据，所有数字必须来自实际运行。**

---

## 1. 测试目标

| 目标 | 说明 |
| --- | --- |
| 核心逻辑单元测试 | 为 `core_engine/thinklab_core/` 中的独立函数建立 pytest 单元测试（B） |
| 输入校验测试 | 对关键输入字段做等价类划分与边界值分析（C） |
| 集成测试 | 验证 API 接口层面的输入校验、错误处理与数据落库（C） |
| 端到端测试 | 覆盖「提问 → 三视角生成 → 选视角 → 多轮对话 → 总结」关键业务流程（D） |
| 覆盖率达标 | 核心逻辑（`thinklab_core`）测试覆盖率 ≥ 60% |

## 2. 测试环境与工具

| 项 | 值 |
| --- | --- |
| Python | 3.12.12（虚拟环境 `code/.venv`） |
| 测试框架 | pytest 9.2.0 |
| 覆盖率 | pytest-cov 7.1.0 / coverage 7.17.3 |
| HTTP 测试客户端 | FastAPI TestClient（依赖 httpx 0.28.1，已随项目安装） |
| 测试数据库 | SQLite（pytest 临时目录，每个测试独立、用后销毁） |
| LLM | 固定 `template` 模式（零网络请求、输出确定；不访问 DeepSeek / OpenAI） |
| 向量库 | 本地 JSON 向量索引（不访问 Pinecone） |
| 运行目录 | 项目根目录 `philosophy-agent/`（`pytest.ini` 所在目录即 rootdir；业务代码位于 `code/`） |

## 3. 测试范围

| 范围 | 是否测试 | 说明 |
| --- | --- | --- |
| `thinklab_core`（lenses / embeddings / memory / chains 检索 / 本地向量库 / 配置解析 / LLM 兜底） | ✅ | 核心逻辑，覆盖率统计对象 |
| `backend/app`（路由、校验、序列化、错误处理） | ✅ | 通过 TestClient 与直接调用测试 |
| DeepSeek / OpenAI 真实调用质量 | ❌ | 无真实密钥；仅测试「缺 key → 模板降级」与 Fake LLM 兜底路径 |
| Pinecone 远程分支 | ❌ | 需真实服务；本地降级分支纳入测试 |
| 前端 `frontend/` | ❌ | 前端无测试设施，不在本次课程范围 |

## 4. 测试分类

### 4.1 单元测试（`tests/unit/`，B 负责）

| 待测对象 | 所在文件 |
| --- | --- |
| 视角画像、阅读规则、无效 key 回退 | `thinklab_core/lenses.py` |
| 哈希向量：确定性、维度、归一化、空输入 | `thinklab_core/embeddings.py` |
| 记忆窗口、压缩阈值、压缩失败回退 | `thinklab_core/memory.py` |
| 检索加权排序、截断、`_safe_json`、`format_context` | `thinklab_core/chains.py`（注入 FakeVectorStore） |
| 本地向量库增删查与持久化 | `thinklab_core/vectorstore.py` |
| 配置解析（`resolved_llm_mode` 等） | `thinklab_core/config.py` |
| LLM 模板模型与兜底开关 | `thinklab_core/llm.py` |
| 入参模型等价类 / 边界值（pydantic 层） | `backend/app/schemas.py` |

### 4.2 集成测试（`tests/integration/`，C 负责）

| 待测对象 | 说明 |
| --- | --- |
| API 输入校验（422 / 400 / 404） | 经真实 HTTP 层验证等价类与边界值 |
| 错误处理与 `X-Request-ID` 响应头 | `app/errors.py` 已实现 |
| 数据落库 | sessions / messages / summaries / retrieval_logs |

### 4.3 端到端测试（`tests/integration/`，D 负责）

| 流程 | 步骤 |
| --- | --- |
| 主业务流程 | 创建探索（三视角）→ 选择视角 → 多轮对话（≥2 轮）→ 生成总结 → 再次对话（验证对话不结束） |
| 流式对话 | SSE 事件序列 `user → token* → done`（含 sources） |

## 5. 测试用例记录表

> 格式约束：编号规则 `B-01`（B 组单测）/ `C-01`（C 组集成）/ `D-01`（D 组端到端）。
> 执行状态只能填：`✅ 通过` / `❌ 失败` / `⏭️ 跳过` / `◻️ 未执行`。

| 编号 | 测试目标 | 输入/操作 | 预期结果 | 实际结果 | 执行状态 |
| --- | --- | --- | --- | --- | --- |
| B-01 | （B 填写） | | | | ◻️ |
| C-01 | （C 填写） | | | | ◻️ |
| D-01 | （D 填写） | | | | ◻️ |

## 6. 测试结果统计

> 以下数字由实际运行自动生成命令输出后填写，禁止手写估算。

| 指标 | 值 |
| --- | --- |
| 单元测试通过 / 总数 | __ / __ |
| 集成测试通过 / 总数 | __ / __ |
| 端到端测试通过 / 总数 | __ / __ |
| 失败用例清单 | （无 / 列出编号） |

## 7. 覆盖率统计

| 指标 | 值 |
| --- | --- |
| 覆盖率统计对象 | `thinklab_core`（配置于项目根目录 `.coveragerc`：`source = thinklab_core`，实际覆盖 `code/core_engine/thinklab_core/`） |
| 总覆盖率（%） | __（待实际运行填写） |
| 覆盖率达标线 | ≥ 60% |
| 未覆盖模块说明 | （如有，注明原因：外部依赖分支 / 数据文件等） |

---

## 附录：常用命令（均在 `code/` 目录执行）

```bash
# 运行全部测试
./.venv/bin/python -m pytest

# 只跑单元测试 / 只跑集成测试（含端到端）
./.venv/bin/python -m pytest tests/unit
./.venv/bin/python -m pytest tests/integration

# 核心逻辑覆盖率（>=60% 时退出码为 0）
./.venv/bin/python -m pytest --cov --cov-fail-under=60

# 覆盖率明细（哪些行未覆盖）
./.venv/bin/python -m pytest --cov --cov-report=term-missing
```

## 附录：fixture 使用说明（B/C/D 参考）

| fixture | 作用 |
| --- | --- |
| `fresh_db` | 每个测试独立的临时 SQLite 数据库（函数级隔离，用后销毁） |
| `db_session` | 绑定临时库的 SQLAlchemy Session（可直接操作 `app.models` 造数） |
| `api_client` | FastAPI TestClient（启动事件已触发、已建表；LLM 为 template 模式，无网络请求） |

环境变量已在 `tests/conftest.py` 顶部统一设置（template LLM、SQLite、无外部服务）。
若个别用例需要其他模式（如关闭兜底、更换 window），请在**测试内**用 `monkeypatch.setenv` +
`thinklab_core.config.reload_settings()`（后端配置用 `app.config.get_settings.cache_clear()`）处理，
不要修改 conftest 或业务代码。
