# ThinkLab 哲学探索 Agent — E2E 测试用例说明

## 一、测试目的

通过端到端（E2E）测试，验证 ThinkLab 哲学探索 Agent 的完整使用流程是否正常，确保用户能够输入问题、选择哲学视角、进行对话、生成思考总结，并在总结后继续对话。

## 二、测试环境

- 操作系统：Windows
- Python 版本：3.12.10
- pytest 版本：9.2.0
- 数据库模式：SQLite
- AI 模式：Template（模板模式）

## 三、测试文件

`tests/integration/test_e2e_philosophy_flow.py`

测试函数：

`test_complete_philosophy_exploration_flow`

## 四、测试用例设计

| 编号 | 测试内容 | 输入或操作 | 预期结果 |
|---|---|---|---|
| E2E-01 | 创建哲学探索会话 | 输入问题：我应该如何面对未来的不确定性？ | 成功创建会话，返回会话信息 |
| E2E-02 | 获取哲学视角 | 请求当前会话的哲学视角列表 | 成功返回哲学视角列表 |
| E2E-03 | 选择哲学视角 | 选择 Stoic（斯多葛主义）视角 | 视角选择成功 |
| E2E-04 | 第一次对话 | 发送第一条消息 | 成功接收用户消息和 Agent 回复 |
| E2E-05 | 第二次对话 | 继续发送消息 | 成功接收新的 Agent 回复 |
| E2E-06 | 生成思考总结 | 请求生成当前会话总结 | 成功生成总结 |
| E2E-07 | 获取总结列表 | 请求当前会话的总结列表 | 成功返回总结记录 |
| E2E-08 | 总结后继续对话 | 总结生成后再次发送消息 | 对话可以正常继续 |
| E2E-09 | 获取会话详情 | 请求当前会话详情 | 成功返回会话信息 |

## 五、测试执行方式

在项目的 `code` 目录下运行：

```bash
python -m pytest tests/integration/test_e2e_philosophy_flow.py -v
```

## 六、测试结果

实际运行命令：

```bash
python -m pytest tests/integration/test_e2e_philosophy_flow.py -v --tb=short
```

实际运行结果：

- 收集测试用例：1 个
- 通过数量：1 个
- 失败数量：0 个
- 执行时间：1.83 秒

测试结果：

`1 passed, 1 warning in 1.83s`

其中，Warning 为 LangChain 旧版 Memory 接口的弃用提示，不影响本次测试通过。

## 七、测试结论

本次端到端测试成功通过。

测试验证了哲学探索 Agent 从创建会话、获取和选择哲学视角、连续对话，到生成思考总结以及总结后继续对话的完整流程。

各项测试断言均通过，说明当前测试环境下系统的主要哲学探索流程能够正常运行。

