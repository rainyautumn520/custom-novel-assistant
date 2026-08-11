# 知识图谱设计（阶段七）

> AI Novel IDE — 面向网文作者的 AI 创作操作系统
>
> 阶段：7 | 状态：基础图谱已实现 | 日期：2026-08-11

## 1. 实体与关系

### 1.1 实体（节点）

| 类型 | 来源表 | 图谱标签 |
|---|---|---|
| setting | settings | 设定 |
| character | characters | 人物 |
| chapter | chapters | 章节 |
| asset | assets | 素材 |
| outline | outline_nodes（v0.3 加入） | 大纲 |

### 1.2 关系（边）

当前统一存于 `entity_links`（relation_type 可扩展）：

| relation_type | 语义 | 建立方式 |
|---|---|---|
| refers_to | 人物引用设定 | 人物编辑页"关联设定" |
| appears_in | 人物/设定出现在章节 | 正文分析（v0.3） |
| belongs_to | 素材属于实体 | 素材关联（v0.3） |
| references | 大纲节点引用设定 | 大纲编辑页（v0.3） |

## 2. 数据流

```text
实体 CRUD（设定/人物/章节/素材）
        │ 写入时
        ▼
   entity_links 表（唯一关系真源）
        │ 读取
        ▼
GET /api/projects/{id}/links
        │ 前端映射
        ▼
   d3-force 力导向图（节点/边/拖拽/悬浮）
```

图谱是**只读投影**：所有关系必须先写入 `entity_links`，前端不做推断。

## 3. 当前实现

- 后端：`GET /api/projects/{id}/links` 返回全部关系；人物↔设定可写（PUT 替换语义）。
- 前端：图谱页加载设定/人物/章节/素材 + 关系，d3-force 渲染，按类型着色，
  支持拖拽与悬浮提示；删除关系由数据源驱动，图谱自动刷新。
- 删除影响提示：删除设定前可查询指向它的 links（MVP 已具备数据基础，UI 待接入）。

## 4. 视觉规范

| 类型 | 颜色 |
|---|---|
| 设定 | 紫 #7c6ff0 |
| 人物 | 蓝 #4aa3ff |
| 章节 | 绿 #4caf7d |
| 素材 | 琥珀 #d9a13b |
| 大纲 | 红 #e05d5d |

节点半径 7px，连线 1px 边框色；节点可拖拽，悬浮显示"类型 · 名称"。

## 5. 演进路线

- **v0.3**：大纲节点入图；正文引用自动提取（规则 + LLM 后验）；删除影响弹窗；
  图谱点击跳转到对应实体页。
- **v0.4**：关系历史（谁在何时建立）、投影重建（从提交链重算 links）。

---

> 相关文档：[README.md](../README.md) · [data-model.md](data-model.md) · [ui-design.md](ui-design.md)
