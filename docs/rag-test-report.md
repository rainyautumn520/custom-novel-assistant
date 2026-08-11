# RAG 测试报告（阶段六）

> AI Novel IDE — 面向网文作者的 AI 创作操作系统
>
> 阶段：6 | 状态：基础检索已验收，向量化待联调 | 日期：2026-08-11

## 1. 测试目标

阶段六要求：准备 RAG 测试数据，验证 AI 理解能力的基础——**检索**。本项目按数据模型约定
分两步走：MVP 用 SQLite LIKE（无模型依赖、零配置），v0.2+ 接入 ChromaDB + BGE-M3 向量检索。

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

## 5. AI 理解能力现状

AI 设定讨论（v0.2 基础）已上线：

- 请求上下文自动加载**已确认设定**（上限 30 条）与最近 20 条会话历史，作为 system prompt。
- 作品级提示词（`ai_system_prompt`）可注入文风/规则要求。
- 无 API Key 时返回 503 并明确提示，不静默失败。
- 结论"纳入设定"必须经人工确认，先存为草稿。

## 6. 向量化接入路径（v0.3，待配置）

1. `requirements.txt` 增加 `chromadb`；本地嵌入模型 BGE-M3 经 Ollama 提供。
2. 每作品库向量目录 `workspaces/<id>/vectors/`（ADR-02 已预留）。
3. 文档→切片→嵌入→ChromaDB；`search` 服务改为 BM25 + 向量混合检索。
4. 章节保存后增量更新向量（数据模型 `file_hash` 可做增量判重）。
5. 联调项：BGE-M3 下载、切片长度、混合检索权重、中文同义召回。

> 诚实说明：向量部分依赖本机嵌入模型与网络，当前未在本次会话下载；上述路径为已裁决的
> 接入方案（见 architecture-decisions.md ADR-02/03），代码入口与数据结构已就绪。

---

> 相关文档：[README.md](../README.md) · [data-model.md](data-model.md) · [architecture-decisions.md](architecture-decisions.md)
