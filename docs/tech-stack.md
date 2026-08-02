# 技术选型说明

> AI Novel IDE — 面向网文作者的 AI 创作操作系统
>
> 版本：v0.1-draft | 日期：2025-07-13

---

## 1. 选型原则

技术选型遵循以下原则：

1. **单一 Agent 全栈负责**：全部开发由 Codex Agent（模型后端：deepseek-v4-flash）统一完成，不做多模型分工
2. **MVP 优先简单**：v0.1 选择最简可行方案，架构预留扩展点
3. **网文作者友好**：客户端打包为桌面应用，安装即用
4. **本地优先**：核心创作数据存本地，AI 调用可选本地模型降级

---

## 2. 前端技术栈

> 开发方式：Codex Agent（deepseek-v4-flash）统一负责前端代码

| 层级 | 选型 | 版本 | 理由 |
|------|------|------|------|
| 语言 | TypeScript | ^5.x | 类型安全，生态成熟，AI 生成质量稳定 |
| UI 框架 | React | ^19.x | 生态最大，组件库丰富，AI 训练数据充分 |
| 桌面壳 | Electron | ^33.x | 跨平台打包（Win/Mac/Linux），Node.js 生态 |
| 构建工具 | Vite | ^6.x | 极速 HMR，Electron 集成成熟 |
| 编辑器 | CodeMirror 6 | ^6.x | 模块化架构，Markdown 支持好，可扩展 |
| 状态管理 | Zustand | ^5.x | 轻量无模板，适合中等复杂度应用 |
| UI 组件 | shadcn/ui + Tailwind | latest | 可定制、可复制、AI 友好 |
| 图谱渲染 | D3.js 或 Cytoscape.js | latest | 力导向图，Obsidian 风格可视化 |
| 图表 | ECharts | ^5.x | 中文生态好，数据分析面板 |

### 为什么不选

| 候选 | 淘汰理由 |
|------|----------|
| Vue | React 生态更大，组件库更丰富，AI 生成样本更充足 |
| Tauri | Rust 学习成本，deepseek-v4-flash 后端已用 Python，不引入第三语言 |
| Next.js | SSR 对桌面端无意义，纯 SPA 即可 |
| Slate.js | API 频繁变动，CodeMirror 更稳定 |
| Redux | 模板过多，Zustand 更简洁 |

---

## 3. 后端技术栈

> 开发方式：Codex Agent（deepseek-v4-flash）统一负责后端代码

| 层级 | 选型 | 版本 | 理由 |
|------|------|------|------|
| 语言 | Python | >=3.12 | deepseek-v4-flash 对 Python 代码生成质量高 |
| Web 框架 | FastAPI | ^0.115 | 异步原生，自动 OpenAPI 文档，Pydantic 集成 |
| 数据校验 | Pydantic v2 | ^2.x | FastAPI 原生集成，性能优异 |
| ORM | SQLAlchemy 2.0 | ^2.x | 异步支持，迁移工具 Alembic |
| 数据库（MVP） | SQLite | 内置 | 零配置，本地存储，适合单用户桌面应用 |
| 数据库（v1.0） | PostgreSQL | ^16 | 多用户、全文搜索、向量扩展 pgvector |
| 迁移工具 | Alembic | latest | SQLAlchemy 官方迁移工具 |
| 向量数据库 | ChromaDB | ^0.5 | 轻量嵌入，Python 原生，无需额外服务 |
| AI 编排 | LangChain | ^0.3 | 生态最大，Agent/RAG 抽象成熟 |
| 本地模型 | Ollama | latest | 离线降级备用；默认统一使用 deepseek-v4-flash |
| 任务队列 | Celery + Redis | latest | Agent 异步任务编排（v0.3+） |

### 为什么不选

| 候选 | 淘汰理由 |
|------|----------|
| Django | 太重，FastAPI 更适合 API 为主的架构 |
| MongoDB | 网文数据高度关系化（人物-世界观-章节），关系型更合适 |
| Pinecone/Weaviate | MVP 阶段引入外部向量服务太重，ChromaDB 嵌入式更轻 |
| LlamaIndex | LangChain 生态更大，Agent 框架更成熟 |
| Flask | 缺少原生异步和自动文档，FastAPI 开发效率更高 |

---

## 4. AI 服务层

| 层级 | 选型 | 用途 |
|------|------|------|
| 规划/架构/Review | deepseek-v4-flash（经 Codex） | PRD、架构设计、代码审查，全栈统一 |
| 后端/RAG/Agent | deepseek-v4-flash（经 Codex） | 业务逻辑生成、RAG 检索、Agent 决策 |
| 前端/UI 代码 | deepseek-v4-flash（经 Codex） | 组件生成、样式实现、TypeScript 代码 |
| 本地嵌入 | BGE-M3 / text2vec | 中文优化，ChromaDB 本地向量化 |
| 本地对话 | deepseek-v4-flash | Ollama 离线降级（备用） |

---

## 5. 开发与 DevOps 工具链

| 工具 | 用途 |
|------|------|
| Codex CLI / Codex 桌面版 | 唯一开发入口 |
| ESLint + Prettier | 前端代码规范 |
| Ruff | Python 代码规范（替代 Flake8 + isort） |
| pytest | Python 测试框架 |
| Vitest | 前端单元测试 |
| Playwright | E2E 测试 |
| electron-builder | 桌面应用打包 |

---

## 6. 技术风险与缓解

| 风险 | 缓解措施 |
|------|----------|
| Electron 内存占用高 | 懒加载、窗口管理、Web Worker 分离编辑器实例 |
| SQLite 并发写入瓶颈 | MVP 单用户无并发问题；v1.0 迁移 PostgreSQL |
| AI API 延迟 | 流式输出（SSE），客户端乐观更新 |
| 向量检索精度不足 | BGE-M3 中文优化 + 混合检索（BM25 + 向量） |
| AI 输出一致性 | Prompt 工程 + 结构化 JSON Schema 约束输出 |

---

> 相关文档：[README.md](../README.md) · [mvp-scope.md](mvp-scope.md) · [architecture.md](architecture.md) · [project-structure.md](project-structure.md) · [dev-setup.md](dev-setup.md)
