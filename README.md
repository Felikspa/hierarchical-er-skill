# hierarchical-er-skill

`hierarchical-er-skill` 是一个围绕“层级化实体关系抽取”构建的完整 skill 产品，是一个“可持续调试、可复盘、可审阅、可增量积累”的 ER skill 工程。它把以下实体关系抽取的环节连接成稳定闭环：

- 自然语言控制抽取粒度
- 结构化实体关系输出
- 证据保留与问题显式暴露
- 规则校验与混合置信度评分
- 跨文档 graph memory 增量记忆
- error set 自动沉淀
- 本地 Web review/debug 面板

用户可以在Codex或Claude Code内直接调用skill，任务完成后可提供一个本地 Web 面板做审阅和人工修订。它不仅从文本里抽实体和关系，还会保留证据、暴露问题、累计图谱记忆、沉淀失败样本。

![image-20260417204704290](C:\Users\24045\AppData\Roaming\Typora\typora-user-images\image-20260417204704290.png)

![image-20260417210639093](C:\Users\24045\AppData\Roaming\Typora\typora-user-images\image-20260417210639093.png)

## 1. 产品亮点与核心特性

### 1.1 三档层级化粒度控制

skill 内置三种固定模式：

- `coarse`
  只输出粗粒度实体和关系，适合快速总览。
- `standard`
  输出业务可读的标准粒度，适合大多数常规分析场景。
- `fine`
  尽可能细地抽取，并强制保留证据，适合精查、debug 和 review。

用户不需要记住参数名，可以直接用自然语言控制：

- `只要粗粒度，抽取这段文本的实体关系`
- `输出业务可读的标准粒度`
- `尽可能细，并保留证据`

### 1.2 结果不只是 JSON，而是完整运行闭环

每次运行后，结果不会停留在临时回复中，而会继续流入本地工程的数据层：

- 运行结果写入 `data/runs/`
- 图谱记忆写入 `data/graph/graph-memory.json`
- 低置信或冲突样本沉淀到 `data/errors/`
- Web review 面板自动读取这些数据

这意味着 skill 会越来越像一个本地知识产品，而不是一次性脚本。

### 1.3 Graph Memory 增量记忆

![image-20260417212133856](C:\Users\24045\AppData\Roaming\Typora\typora-user-images\image-20260417212133856.png)

系统会将多次运行中的实体和关系增量写入本地 graph memory，用于跨文档归一和持续积累。

归一规则优先级固定为：

1. 规范名一致
2. 别名命中
3. 类型兼容且字符串归一相似
4. 已知实体映射命中

它不做“模糊猜测式兜底”，而是尽量用规则化、可解释的方式做归一。

### 1.4 Error Set 自动沉淀

当出现以下情况时，系统会自动将样本沉淀为错误案例：

- 综合置信度过低
- 发生规则冲突或证据冲突
- 人工 review 后发生实质性修改

每个 error case 会带上：

- 原文
- 原始抽取结果
- 置信度摘要
- issue 信息
- review 修订结果
- few-shot 标签建议
- prompt 优化建议

这为后续继续优化 schema、skill 提示词或评测集提供稳定素材。

### 1.5 可编辑、可追踪的本地 Web 面板

项目自带一个无构建步骤的本地 Web 面板，面向“审阅与 debug”：

- 查看原文与 chunk
- 查看实体和关系
- 查看证据片段
- 查看置信度分层
- 查看 issue 列表
- 查看历史运行
- 查看 graph memory 增量摘要
- 查看 error set 命中情况
- 直接做人工 review 并保存修订

## 2. 部署与操作指南

### 2.1 环境要求

当前版本默认面向Claude Code或Codex 工作流，使用：

- Python 3.11+ 或兼容版本
- Git
- 浏览器

前端和后端都不依赖额外第三方包，Python 标准库即可运行。

### 2.2 获取并安装skill

只需在Codex的对话中输入“帮我安装以下目录中的skill：https://github.com/Felikspa/hierarchical-er-skill.git”。

安装完成后，Codex 可通过以下两种方式使用它：

- 显式调用：`$hierarchical-er-skill`
- 隐式调用：用符合触发语义的自然语言直接提需求

### 2.3 如何用自然语言控制粒度

skill 内部会把自然语言请求映射到三档模式。

#### 触发 `coarse`

适合快速总览。

示例：

- `只要粗粒度，抽取这段文本的实体关系`
- `先给我一个高层摘要版的 ER 结果`

#### 触发 `standard`

适合业务可读输出。

示例：

- `输出业务可读的标准粒度`
- `帮我抽取这段文本中的实体和关系，结果清晰一些`

#### 触发 `fine`

适合精细抽取和调试。

示例：

- `尽可能细，并保留证据`
- `用最细粒度抽取，并把证据一起列出来`

如果用户没有明确说粒度，默认走 `standard`。

### 2.4 如何启动 Web 面板

直接让codex启动Web服务，面板会自动弹出。或者手动启动：

#### 方式一：直接启动服务并自动打开浏览器

```powershell
python hierarchical-er-skill\scripts\serve_review_app.py --host 127.0.0.1 --port 8765
```

默认地址：

- `http://127.0.0.1:8765/`

#### 方式二：只生成当前状态，不开服务

```powershell
python hierarchical-er-skill\scripts\serve_review_app.py --build-state
```

这个命令会打印面板当前需要读取的数据摘要，适合调试接口。

### 2.5 完整本地处理链路

如果你已经有一个符合协议的运行结果 JSON，可以依次执行：

```powershell
python hierarchical-er-skill\scripts\validate_output.py hierarchical-er-skill\data\runs\seed-run.json
python hierarchical-er-skill\scripts\check_constraints.py hierarchical-er-skill\data\runs\seed-run.json --write
python hierarchical-er-skill\scripts\score_confidence.py hierarchical-er-skill\data\runs\seed-run.json --write
python hierarchical-er-skill\scripts\update_graph_memory.py hierarchical-er-skill\data\runs\seed-run.json
python hierarchical-er-skill\scripts\capture_error_case.py hierarchical-er-skill\data\runs\seed-run.json
python hierarchical-er-skill\scripts\report_regression.py
python hierarchical-er-skill\scripts\serve_review_app.py --port 8765
```

每一步分别负责：

1. 校验输出协议是否完整
2. 检查关系约束、方向、允许配对和跨句窗口
3. 计算混合置信度
4. 更新本地 graph memory
5. 判断是否沉淀错误案例
6. 跑回归检查
7. 打开 review/debug 面板

### 2.6 日常使用建议

对于普通使用者，推荐工作流是：

1. 在 Codex 中直接用自然语言描述任务
2. 让 skill 产出结构化结果
3. 打开 Web 面板检查证据、置信度和 issues
4. 在 Web 面板中做人审修订
5. 让修改进入 revision 和 error set 统计

对于开发者，推荐工作流是：

1. 修改 schema / 脚本 / 前端
2. 跑种子样本和回归
3. 打开 Web 面板检查可视化和 review 流程
4. 根据 error set 继续迭代

## 3. 具体使用示例

### 3.1 示例原文

下面是当前工程自带的种子示例文本，来自 [seed-run.json](C:\Users\24045\Desktop\Identities\hierarchical-er-skill\data\runs\seed-run.json)：

```text
飞书研发负责人林岚在上海发布会上表示，飞书数据平台 Atlas 将于 5 月上线。
她提到 Atlas 由飞书数据团队维护，并服务于企业知识检索场景。
```

### 3.2 示例一：粗粒度调用

用户输入：

```text
只要粗粒度，抽取这段文本的实体关系。
```

预期效果：

- 只保留高层实体，比如 `person`、`organization`、`location`、`product`、`event`
- 关系数量较少，结果更适合快速浏览
- 不追求把角色、时间、部门、技术等细粒度信息全部展开

预期输出风格：

```json
{
  "mode": "coarse",
  "entities_coarse": [
    { "canonical_name": "林岚", "label": "person" },
    { "canonical_name": "飞书", "label": "organization" },
    { "canonical_name": "上海", "label": "location" },
    { "canonical_name": "Atlas", "label": "product" },
    { "canonical_name": "上海发布会", "label": "event" }
  ],
  "relations_coarse": [
    { "type": "affiliated_with", "head": "林岚", "tail": "飞书" },
    { "type": "located_in", "head": "上海发布会", "tail": "上海" }
  ]
}
```

### 3.3 示例二：标准粒度调用

用户输入：

```text
输出业务可读的标准粒度。
```

预期效果：

- 除粗粒度结果外，会补充更适合业务理解的结构
- 比如组织、部门、角色、事件、产品之间的业务关系
- 结果适合直接人工阅读和分析

预期输出重点：

- 结果比 `coarse` 更细
- 但不会像 `fine` 一样尽量穷尽每一条细项证据

### 3.4 示例三：细粒度调用

用户输入：

```text
尽可能细，并保留证据。
```

预期效果：

- 输出完整的 `entities_fine` 和 `relations_fine`
- 每个实体和关系都带 `evidence_ids`
- 低置信项、规则冲突会被写入 `issues`
- 后处理脚本会刷新 graph memory 和 error set

当前种子样本中的细粒度结果可从 [seed-run.json](C:\Users\24045\Desktop\Identities\hierarchical-er-skill\data\runs\seed-run.json) 看到，典型实体包括：

- `林岚 / person`
- `飞书 / organization`
- `研发负责人 / role`
- `上海 / location`
- `上海发布会 / event`
- `Atlas / product`
- `5 月 / time`
- `飞书数据团队 / department`
- `企业知识检索 / technology`

典型关系包括：

- `affiliated_with(林岚 -> 飞书)`
- `participates_in(林岚 -> 上海发布会)`
- `located_in(上海发布会 -> 上海)`
- `scheduled_at(上海发布会 -> 5 月)`
- `member_of(飞书数据团队 -> 飞书)`
- `owns(飞书 -> Atlas)`
- `uses(Atlas -> 企业知识检索)`

### 3.5 预期的产品级效果

一次完整运行后，预期同时得到：

- 一份稳定 JSON 结构化结果
- 一份显式 issue 列表
- 一份分层置信度结果
- 一次 graph memory 更新
- 一次 error capture 判断
- 一个可在 Web 面板中继续人工审阅的状态

## 4. Web 面板详细功能说明

### 4.1 历史运行切换

左侧 `历史运行` 区域会列出所有 run。

你可以：

- 切换到某次历史运行
- 比较不同时间的抽取状态
- 检查某次运行是否已经被 review
- 检查它是否命中过 error set

### 4.2 原文与 chunk 视图

面板中部的 `原文与证据` 区域会展示：

- 原始文本 chunk
- sentence 范围
- 证据卡片

当选择某个实体时，原文中对应 span 会被高亮，帮助你对照抽取位置。

### 4.3 实体结果区

`实体结果` 区域会展示当前模式下的实体列表。

你可以快速看到：

- 实体 ID
- 实体 label
- canonical name
- 原始 text

如果后续你在 review 中改了实体 label 或 canonical name，这里就会成为重点检查区域。

### 4.4 关系结果区

`关系结果` 区域会展示当前模式下的关系列表。

你可以看到：

- relation type
- head / tail
- direction
- relation id

它适合重点检查：

- head/tail 是否接反
- relation type 是否选错
- 方向字符串是否与 schema 一致

### 4.5 置信度分层

`置信度分层` 区域会显示实体和关系的综合评分。

评分来自固定混合公式，来源包括：

- 模型自评分
- 证据充分性
- 规则一致性
- 冲突惩罚

当前阈值：

- `low < 0.65`
- `medium = 0.65 ~ 0.84`
- `high >= 0.85`

这个区域适合快速定位“最值得先审”的条目。

### 4.6 冲突与问题

`冲突与问题` 区域会列出所有 `issues`。

当前系统会显式记录的典型问题包括：

- 未知关系类型
- 实体引用缺失
- 非法实体配对
- 方向不匹配
- 跨句窗口超限
- 重复关系
- 低置信项

这里是最重要的 debug 入口之一。

### 4.7 Graph Memory 增量摘要

`Graph Memory 增量摘要` 会告诉你：

- 本次运行匹配了多少已有实体
- 新增了多少图谱实体
- 新增了多少图谱关系
- 当前 graph memory 的总体规模

它可以帮助你判断跨文档归一是否稳定，以及图谱是否在持续积累。

### 4.8 Error Set 区域

`Error Set` 区域会展示：

- 当前运行是否被判定为错误案例
- 命中的原因
- case id
- few-shot 标签建议
- prompt 优化建议

这不是“报错页面”，而是面向后续产品迭代的学习层。

### 4.9 如何进行人工 Review

当前 Web 面板支持直接人工修订。

#### Review 的基本步骤

1. 打开目标运行
2. 选择合适的模式视图：`coarse` / `standard` / `fine`
3. 在 `人工 Review` 区域修改实体或关系
4. 如有需要填写 `Review note`
5. 点击 `保存修订`

#### 当前可编辑项

实体支持编辑：

- `label`
- `canonical_name`

关系支持编辑：

- `type`
- `head_id`
- `tail_id`
- `direction`

#### 保存后会发生什么

保存 review 后，系统会：

1. 生成 `*.review.json` 修订文件
2. 更新原始 run 的 `review_status`
3. 重新评估是否需要进入 `error set`
4. 如果命中规则，写入或更新 error case

#### 什么情况下 review 会触发错误样本沉淀

当满足以下任一条件时：

- 实质修改数 `>= 2`
- 修改比例 `>= 30%`

这保证“改动很大”的样本不会悄悄丢失，而会进入后续迭代资料库。

## 5. 面向开发者的技术说明

### 5.1 项目目录结构

```text
.
├── PLAN.md
├── README.md
├── PRODUCT_DEMO.md
└── hierarchical-er-skill/
    ├── SKILL.md
    ├── agents/
    │   └── openai.yaml
    ├── schema/
    │   └── schema.yaml
    ├── contracts/
    │   ├── output.schema.json
    │   ├── error-case.schema.json
    │   └── graph-memory.schema.json
    ├── references/
    │   ├── workflow.md
    │   └── web-panel.md
    ├── scripts/
    │   ├── common.py
    │   ├── validate_output.py
    │   ├── check_constraints.py
    │   ├── score_confidence.py
    │   ├── update_graph_memory.py
    │   ├── capture_error_case.py
    │   ├── report_regression.py
    │   └── serve_review_app.py
    ├── data/
    │   ├── runs/
    │   ├── graph/
    │   ├── errors/
    │   └── regression/
    └── webapp/
        ├── index.html
        ├── styles.css
        ├── app.js
        └── components/
```

### 5.2 关键模块说明

#### `SKILL.md`

skill 的行为定义入口，约束：

- 何时触发
- 如何映射粒度
- 必须读取哪些 schema/contract/reference
- 后处理脚本的固定执行顺序

#### `schema/schema.yaml`

这里实际存放的是 JSON 结构内容，用于描述：

- 三档模式的实体/关系层级
- label alias
- relation alias
- 允许配对
- 方向规则
- 跨句窗口
- 置信度阈值
- review 判定阈值

#### `contracts/`

负责固定数据协议，当前包含：

- `output.schema.json`
  单次运行输出结构
- `error-case.schema.json`
  错误案例结构
- `graph-memory.schema.json`
  图谱记忆结构

#### `scripts/`

后端逻辑全部在这里。

- [common.py](C:\Users\24045\Desktop\Identities\hierarchical-er-skill\scripts\common.py)
  公共路径、数据读写、索引、review diff 逻辑
- [validate_output.py](C:\Users\24045\Desktop\Identities\hierarchical-er-skill\scripts\validate_output.py)
  基础协议校验
- [check_constraints.py](C:\Users\24045\Desktop\Identities\hierarchical-er-skill\scripts\check_constraints.py)
  关系约束检查
- [score_confidence.py](C:\Users\24045\Desktop\Identities\hierarchical-er-skill\scripts\score_confidence.py)
  混合置信度计算与低置信 issue 生成
- [update_graph_memory.py](C:\Users\24045\Desktop\Identities\hierarchical-er-skill\scripts\update_graph_memory.py)
  增量图谱归一与写入
- [capture_error_case.py](C:\Users\24045\Desktop\Identities\hierarchical-er-skill\scripts\capture_error_case.py)
  错误样本评估与落盘
- [report_regression.py](C:\Users\24045\Desktop\Identities\hierarchical-er-skill\scripts\report_regression.py)
  基于黄金样本做回归对比
- [serve_review_app.py](C:\Users\24045\Desktop\Identities\hierarchical-er-skill\scripts\serve_review_app.py)
  本地 HTTP 服务与 review API

#### `webapp/`

原生前端，无构建步骤。

- `index.html`
  页面骨架
- `styles.css`
  视觉设计与响应式布局
- `app.js`
  主状态管理与数据请求
- `components/`
  按面板区域拆分的 UI 组件

### 5.3 数据流

当前产品的数据流是单向而清晰的：

1. skill 或脚本写入 `data/runs/*.json`
2. 校验、评分、graph 更新、error capture 继续写本地数据
3. Web 面板只读这些 JSON 数据
4. review 保存走本地 HTTP API
5. API 再把修订结果写回 `data/runs/` 与 `data/errors/`

浏览器本身不参与抽取，只负责展示和人工修订。

