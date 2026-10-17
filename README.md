# 哲学代理人 philosophy-agent
> 面向哲学学习者的AI思辨代理项目

## 项目简介
哲学代理人是一款AI对话代理，面向哲学专业学生与哲学爱好者。
本工具可以辅助哲学学习，辨析哲学概念、梳理不同哲学家的理论观点，通过对话引导用户进行批判性思辨，辅助哲学论文写作与哲学探究练习。

## 分支管理策略
- `main`：主分支，存放稳定、验收完成的最终版本，禁止直接提交代码。
- `develop`：开发分支，所有文档编写、代码开发、功能迭代都在此分支进行，开发完成后通过PR合并至main。

## 项目目录结构
├── docs/ # 项目文档
│ ├── requirements/ # 需求文档
│ │ └── problem_definition.md # 5W1H 问题定义文档
│ ├── algorithm/ # 算法设计文档
│ ├── software/ # 软件设计文档
│ ├── mgmt/ # 项目管理文档
│ └── retrospection/ # 项目复盘文档
├── code/ # 源代码
│ ├── backend/ # 后端代码
│ ├── frontend/ # 前端代码
│ └── core_engine/ # AI 核心引擎
├── tests/ # 测试代码
│ ├── unit/ # 单元测试
│ └── integration/ # 集成测试
├── .github/workflows/ # CI 自动化配置
└── README.md # 项目说明文档

## 任务与项目管理
- 使用 GitHub Issues 进行任务与缺陷(Bug)跟踪
- 使用 Kanban 看板「哲学代理看板」管理开发任务，分为：待办、进行中、已完成三列

## 团队信息
项目名称：哲学代理人
