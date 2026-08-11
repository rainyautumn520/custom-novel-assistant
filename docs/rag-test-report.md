# RAG 测试报告（阶段六）

> AI Novel IDE — 面向网文作者的 AI 创作操作系统
>
> 阶段：6 | 状态：基础检索已验收，向量化待联调 | 日期：2026-08-11

## 1. 测试目标

阶段六要求：准备 RAG 测试数据，验证 AI 理解能力的基础——**检索**。本项目已实现两级检索：
词法检索（SQLite ILIKE，零依赖）与**向量检索**（ChromaDB + BGE-small-zh-v1.5，本地嵌入）。

## 2. 测试数据

生成脚本：[scripts/seed_rag_data.py](../apps/server/scripts/seed_rag_data.py)

```text
项目：性能验收测试书（玄幻）
├── 设定 15 条（confirmed）
├── 人物 10 名
├── 素材 50 条
└── 大纲：3 卷 × 10 章 = 30 章，每章正文 10,000 字符
```

## 3. 检索实现（当前）

`POST /api/projects/{project_id}/search`：

- 范围：设定（标题/正文/标签）、人物（姓名/身份/背景）、素材（标题/正文/标签）。
- 实现：SQLite `ILIKE` 多字段匹配，返回类型、标题、摘要。
- 定位：BM25/向量检索上线前的轻量版本，满足 MVP 搜索与"来源可见"基础。

## 4. 验收结果（2026-08-11 实跑）

| 指标 | 结果 | PRD 目标 | 结论 |
|---|---|---|---|
| 数据生成 | 30 章 / 77,400 非空字符，1.02s | — | 通过 |
| 检索耗时 | 6.6 ms | 5,000 条 < 500 ms | 通过 |
| 章节列表 | 1.8 ms | — | 通过 |
| 检索命中 | 查询"灵脉"命中 75 条 | — | 通过 |

## 5. 向量检索实现（已完成）

- 存储：每作品 `workspaces/<id>/vectors/`（ChromaDB PersistentClient，cosine 距离）。
- 嵌入后端可切换（`AI_NOVEL_VECTOR_BACKEND`）：
  - `sentence-transformers`（默认）：BAAI/bge-small-zh-v1.5，约 100 MB，CPU 推理。
  - `ollama`：`bge-m3`（本机 Ollama 已安装，模型拉取后切换环境变量即可）。
- 索引范围：已确认设定、人物、素材、章节正文；切片 300 字、重叠 50 字。
- 增量：章节保存后自动更新该章向量（`index_chapter`，失败不阻断保存）；全量重建走
  `POST /api/projects/{id}/rag/index`。
- 检索：`POST /api/projects/{id}/rag/search`，返回类型、标题、摘要与余弦分数。
- AI 讨论已接入：system prompt 自动携带「相关检索」top-8，替代固定取前 30 条设定。

## 6. 验收结果（2026-08-11 实跑，sentence-transformers 后端）

| 指标 | 结果 | 说明 |
|---|---|---|
| 索引规模 | 405 个向量块（30 章 + 15 设定 + 10 人物 + 50 素材） | 24.66 s（模型已缓存） |
| 向量检索 | 78 ms / 查询 | 远低于交互阈值 |
| 语义命中 | "灵脉枯竭的真相" → 设定15·灵气复苏规则（0.54） | 语义理解有效 |
| 词法检索 | 4.6 ms | 与向量混合可用 |

## 7. AI 理解能力现状

AI 设定讨论（v0.2 基础）已上线：

- 请求上下文自动加载**已确认设定**（上限 30 条）与最近 20 条会话历史，作为 system prompt。
- 作品级提示词（`ai_system_prompt`）可注入文风/规则要求。
- 无 API Key 时返回 503 并明确提示，不静默失败。
- 结论"纳入设定"必须经人工确认，先存为草稿。

## 8. 后续优化（v0.3）

1. BM25 + 向量混合排序与权重调优。
2. 设定/人物/素材的写操作增量更新（当前章节已增量，其余靠重建）。
3. 切换 Ollama bge-m3 后对比中文召回率（1024 维 vs 512 维）。
4. 切片长度与重叠参数按题材微调。

---

> 相关文档：[README.md](../README.md) · [data-model.md](data-model.md) · [architecture-decisions.md](architecture-decisions.md)
