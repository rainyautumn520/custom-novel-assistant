# AI Novel IDE

> 面向网文作者的 AI 创作操作系统
>
> 融合 Obsidian 知识图谱 + Notion 资料管理 + Codex AI 协作

---

## 项目愿景

AI Novel IDE 是一个专为网文作者设计的全流程创作工具。它将世界观设定、人物塑造、大纲编排、正文撰写、素材管理和 AI 辅助整合到一个统一的工作台中，让作者专注于创作本身而非工具切换。

### 解决的核心问题

| 痛点 | 现状 | AI Novel IDE |
|------|------|-------------|
| 设定分散 | 多个文档/笔记软件存放 | 统一的结构化设定管理 |
| 前后矛盾 | 人工记忆和回溯 | AI 基于 RAG 自动检查一致性 |
| 缺乏反馈 | 写完才找人审稿 | 内置编辑 Agent 实时建议 |
| 数据盲区 | 不知道自己写作习惯 | 数据分析面板可视化产出 |

---

## 核心设计理念

- **Obsidian 的知识图谱**：人物、地点、事件以节点-边形式可视化，自由双向链接
- **Notion 的资料管理**：世界观、角色卡、素材的结构化数据库，灵活检索
- **Codex 的 AI 协作**：上下文感知的智能补全、改写建议、一致性检查

---

## 子系统架构

```
AI Novel IDE
├── 世界观系统    → 规则、地理、历史、势力设定
├── 人物系统      → 角色卡、关系网络、成长弧线
├── 大纲系统      → 层级化大纲（卷→章→节）
├── 正文编辑器    → 分章写作、Markdown 预览、版本管理
├── 素材库        → 参考资料、灵感片段集中管理
├── AI Agent      → 编剧 / 作者 / 编辑 / 数据分析 Agent
├── RAG 知识库    → 全量设定和正文的 AI 上下文检索
├── 知识图谱      → Obsidian 风格可视化实体关系图
├── 节奏分析      → 字数、情节密度、高潮间隔统计
└── 数据分析      → 写作习惯、产出效率数据面板
```

---

## 技术栈

全栈统一由 Codex Agent（模型后端：deepseek-v4-flash）负责：

| 层 | 技术 |
|----|------|
| 产品规划 / 架构 | 文档驱动，Codex 规划与评审 |
| 前端 / UI | React + TypeScript + Electron |
| 后端 / 数据库 / RAG / Agent | Python FastAPI + SQLite + ChromaDB + LangChain |
| 代码审查 | Codex 统一审查（不再多模型分工） |

详见 [tech-stack.md](docs/tech-stack.md)

---

## 开发阶段

| 阶段 | 内容 | 文档产出 |
|------|------|----------|
| 阶段 0（已完成） | 明确 MVP 范围 + 创建项目文档 | 本文档套件 |
| 阶段 1（已完成） | Codex 设计 PRD + 审核功能和页面结构 | PRD + 页面结构审核 |
| 阶段 2（已完成） | Codex 确定技术架构 + 检查扩展性 | 架构设计 + 技术决策记录 |
| 阶段 3（已完成） | 设计数据结构（小说/人物/世界观/章节/素材/关系） | 数据模型 |
| 阶段 4（已完成） | 确定 UI 风格（Obsidian / Codex / Notion 融合） | UI 设计稿 + 可点击原型 |
| 阶段 5（MVP 已完成） | 分配开发任务 + 测试功能 + 记录 Bug | 设定/人物/大纲/正文/素材/导出 + AI 讨论 + 封面工坊 + 图谱 |
| 阶段 6（基础检索已验收） | 准备 RAG 测试数据 + 验证 AI 理解能力 | RAG 测试报告（向量化待 v0.3） |
| 阶段 7（已完成） | 定义知识图谱关系 | 图谱设计 + 基础力导向图 |
| 阶段 8（已完成） | 定义 Agent 职责 | Agent 设计 |

---

## 快速导航

| 文档 | 说明 |
|------|------|
| [产品需求文档（PRD）](docs/prd.md) | 阶段一产品基线、版本范围、功能需求与验收标准 |
| [功能与页面结构审核](docs/information-architecture.md) | 信息架构、页面合同、跨页流程与审核结论 |
| [MVP 范围定义](docs/mvp-scope.md) | MoSCoW 优先级矩阵、版本路线、风险假设 |
| [技术选型说明](docs/tech-stack.md) | 前端/后端/AI 三层选型与理由 |
| [架构概览](docs/architecture.md) | 五层架构、子系统职责、数据流 |
| [技术决策记录（ADR）](docs/architecture-decisions.md) | 进程拓扑、数据隔离、正文存储、密钥、Seedream 等裁决 |
| [数据模型设计](docs/data-model.md) | 表结构、关系、状态机、迁移与删除规则 |
| [UI 设计稿](docs/ui-design.md) | 设计令牌、五区布局、组件规范、页面线框与交互规则 |
| [UI 可点击原型](prototype/index.html) | 七个核心页面的 HTML 原型，双击本地打开即可浏览 |
| [RAG 测试报告](docs/rag-test-report.md) | 检索 API 验收数据与结果、向量化接入路径 |
| [知识图谱设计](docs/graph-design.md) | 实体/关系类型、数据流、视觉规范与演进路线 |
| [Agent 设计](docs/agent-design.md) | Context/Writer/Reviewer/Data 角色职责与落地清单 |
| [项目目录结构](docs/project-structure.md) | monorepo 推荐布局 |
| [开发环境搭建](docs/dev-setup.md) | 环境要求、启动步骤、推荐插件 |

---

## 开发环境快速开始

```bash
# 前置要求
Node.js >= 20
Python >= 3.12
Git

# 克隆仓库
git clone <repo-url>
cd custom-novel-assistant

# 安装前端依赖（npm workspaces，含 Electron）
npm install

# 后端
cd apps/server
python -m venv .venv
.\.venv\Scripts\pip install -r requirements.txt   # Windows
source .venv/bin/pip install -r requirements.txt  # macOS/Linux

# 一键启动（Windows）
cd ../..
powershell -ExecutionPolicy Bypass -File scripts/dev.ps1

# 或分两个终端手动启动：
# 终端 1：后端
cd apps/server
.\.venv\Scripts\python -m uvicorn app.main:app --reload --port 8000
# 终端 2：前端（浏览器调试）
cd ../..
npm run dev:desktop
# 终端 2 备选：Electron 桌面窗口
npm run electron:dev -w @ai-novel-ide/desktop
```

验证：后端 API 文档 http://localhost:8000/docs；前端 http://localhost:5173。
详见 [dev-setup.md](docs/dev-setup.md) 与 [project-structure.md](docs/project-structure.md)。

---

## 许可证

MIT

---

> 版本：v0.5 | 阶段八完成日期：2026-08-11
