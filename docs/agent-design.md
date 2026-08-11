# Agent 设计（阶段八）

> AI Novel IDE — 面向网文作者的 AI 创作操作系统
>
> 阶段：8 | 状态：已定稿 | 日期：2026-08-11

## 1. 设计原则

参考 webnovel-writer 的最小可用分工：**读上下文 → 写正文 → 审质量 → 入账**。
本项目由 Codex（deepseek-v4-flash）统一承担开发与 AI 能力，产品侧按角色拆分职责，
便于上下文隔离与审计。

## 2. 角色与职责

| Agent | 职责 | 输入 | 输出 | 现状 |
|---|---|---|---|---|
| Context Agent | 写前研究，输出"写作任务书" | 章纲合同、已确认设定、相关人物、时间线 | 任务书（目标/人物/约束/收尾点） | 设定讨论上下文已实现；任务书待 v0.3 |
| Writer Agent | 续写/改写建议 | 任务书 + 当前正文 + 章纲合同 | 建议文本（差异预览） | AI 讨论已具备基础；编辑器内联待做 |
| Reviewer Agent | 五维审查 | 正文 + 设定 + 章纲 | 结构化审查结果 | 未实现（v0.3） |
| Data Agent | 写后提取事实/状态变更 | 提交的正文 | chapter-commit（事件/实体增量） | 未实现（v0.4 提交链） |

## 3. 上下文与记忆策略

1. **合同驱动**：写作前必须加载章纲合同（目标/必须覆盖/禁区），设定取 `confirmed`。
2. **少带多查**：不把全书塞进上下文；通过检索 API 只取相关实体。
3. **人工确认**：AI 结论进入正式数据前必须预览确认（"纳入设定"已是此模式）。
4. **投影分离**：对话、检索、向量都是可重建投影；正式数据只有 DB + 文件。

## 4. 与 Codex 的协作

- 开发侧：Codex 统一负责代码生成/审查（tech-stack.md）。
- 产品侧：AI 能力以 API 形式嵌入（`/api/projects/{id}/ai/*`），前端只做展示与确认。
- 提示词管理：全局配置 + 作品级 `ai_system_prompt`（已实现）。

## 5. v0.3 落地清单

1. 编辑器内联"续写/改写"（选中文本 → 差异预览 → 应用/撤销）。
2. Reviewer 五维审查：设定一致性、时间线、叙事连贯、角色一致性、逻辑。
3. 章纲合同写入任务书模板。
4. 审查结果结构化落库（复用 ai_messages 或新增 review 表）。

## 6. v0.4 落地清单

1. Data Agent：章节提交后提取新增实体/事件 → `entity_links` 自动建边。
2. chapter-commit：状态机 `draft → committed`，提交后投影重建。
3. 项目体检（doctor）：检查悬空引用、断档伏笔、设定冲突。

---

> 相关文档：[README.md](../README.md) · [rag-test-report.md](rag-test-report.md) · [graph-design.md](graph-design.md) · [architecture-decisions.md](architecture-decisions.md)
