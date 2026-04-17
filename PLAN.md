# `hierarchical-er-skill` 工程实施计划 v2

## Summary
- 在当前目录构建一个完整工程：`Codex skill + 本地增量记忆层 + 可编辑可视化 Web 应用 + 回归/错误集工具链 + README 演示文档`。
- skill 面向“自然语言任务说明 + 纯文本输入”调用，默认支持三档粒度控制：`粗粒度`、`标准粒度`、`尽可能细并保留证据`。
- 每次运行后不只产出单文抽取结果，还会：
  - 写入标准化 JSON 结果
  - 更新跨文档图谱记忆
  - 记录运行历史
  - 生成/刷新本地 Web 面板并打开
  - 自动沉淀失败样本到 `error set`
- v1 不做训练或自动改 prompt，只做到“失败样本自动沉淀 + few-shot/prompt 更新建议 + 可回放案例包”；不加入任何静默兜底。

## Project Layout
- `README.md`
  - 面向演示讲解，说明项目价值、产品亮点、运行流程、输出结果、Web 面板、失败样本闭环、图谱增量记忆、Codex 接入方式。
- `hierarchical-er-skill/`
  - 真正被 Codex 发现的 skill 根目录。
- `hierarchical-er-skill/SKILL.md`
  - 触发条件、粒度控制器、抽取流程、冲突检查、失败样本沉淀、图谱记忆更新、何时刷新 Web。
- `hierarchical-er-skill/agents/openai.yaml`
  - `$hierarchical-er-skill` 的 UI 元数据与默认 prompt，允许隐式调用。
- `hierarchical-er-skill/schema/schema.yaml`
  - 粗粒度/标准粒度/细粒度的实体与关系层级、别名映射、允许配对、方向规则、局部跨句窗口。
- `hierarchical-er-skill/contracts/output.schema.json`
  - 单次运行结果的稳定输出协议。
- `hierarchical-er-skill/contracts/error-case.schema.json`
  - 失败样本包协议。
- `hierarchical-er-skill/contracts/graph-memory.schema.json`
  - 增量图谱记忆协议。
- `hierarchical-er-skill/references/workflow.md`
  - skill 执行顺序、粒度切换规则、置信度定义、冲突修正规则。
- `hierarchical-er-skill/references/web-panel.md`
  - Web 面板的信息架构、交互规则、人工 review 流程。
- `hierarchical-er-skill/scripts/`
  - `validate_output.py`：校验运行结果 JSON。
  - `score_confidence.py`：计算混合置信度。
  - `check_constraints.py`：检查实体/关系/粒度/方向冲突。
  - `update_graph_memory.py`：按规则更新跨文档图谱记忆。
  - `capture_error_case.py`：把失败样本写入 error set。
  - `report_regression.py`：回归比对。
  - `serve_review_app.py`：启动本地 Web 应用并打开浏览器。
- `hierarchical-er-skill/data/`
  - `runs/`：每次运行的结果、修订版、元信息。
  - `graph/graph-memory.json`：跨文档实体归一和关系增量更新结果。
  - `errors/error-set.jsonl`：失败样本索引。
  - `errors/cases/`：可回放案例包。
  - `regression/cases/`：人工精选黄金样本。
- `hierarchical-er-skill/webapp/`
  - 原生 HTML/CSS/JS 本地小型 Web 应用，无构建步骤。
  - `index.html`、`styles.css`、`app.js`、`components/*.js`、`assets/*`。

## Implementation Changes
- skill 执行流程固定为 7 步：
  1. 解析用户请求，映射到三档粒度模式之一。
  2. 读取对应 schema 视图和输出要求。
  3. 执行多粒度实体关系抽取，默认保留证据。
  4. 运行约束校验与确定性修正。
  5. 计算混合置信度并标记低置信项。
  6. 更新图谱增量记忆与失败样本集。
  7. 写入本次运行数据，刷新并打开本地 Web 面板。
- 粒度控制器固定支持三档：
  - `coarse`：只输出粗粒度实体与关系。
  - `standard`：输出业务可读标准粒度。
  - `fine`：输出尽可能细的结果，并强制保留证据。
- 失败样本自动沉淀规则固定为 3 类：
  - 综合置信度低于阈值。
  - 发生规则冲突或证据冲突。
  - 人工 review 保存后存在实质性修改。
- 错误集不直接改写 skill；v1 只负责沉淀可回放案例包，并额外生成 few-shot/prompt 更新建议文件。
- 图谱增量记忆以本地 JSON 仓库实现，采用规则优先归一：
  - 规范名一致
  - 别名命中
  - 类型兼容
  - 字符串归一相似
  - 已知实体映射命中
- Web 应用定位为“审阅与 debug 面板”，每次运行更新数据源并自动打开，不生成一次性孤立页面。
- UI 风格固定走“精致、简洁、偏专业数据产品”的方向：
  - 浅色为默认主题
  - 明确信息层级与留白
  - 细腻但克制的动效
  - 强调表格、关系图、证据卡片和冲突提示的可扫读性
- 面板必须包含这些主区域：
  - 原文与 chunk 视图
  - 实体 span 高亮
  - 关系边与图谱视图
  - 置信度分层
  - 冲突点与 issue 列表
  - 人工 review 编辑区
  - 历史运行切换
  - graph memory 增量摘要
  - error set 命中与沉淀记录

## Public Interfaces
- skill 名称固定为 `$hierarchical-er-skill`。
- 运行结果顶层 JSON 固定字段：
  - `run_id`
  - `created_at`
  - `input_text`
  - `mode`
  - `language`
  - `schema_version`
  - `chunks`
  - `entities_coarse`
  - `entities_fine`
  - `relations_coarse`
  - `relations_fine`
  - `evidence`
  - `confidence`
  - `issues`
  - `graph_updates`
  - `error_capture`
  - `review_status`
- `confidence` 采用混合评分，来源固定为：
  - 模型自评分
  - 证据充分性
  - 规则一致性
  - 冲突惩罚
- 默认阈值：
  - `low_confidence < 0.65`
  - `medium_confidence 0.65–0.84`
  - `high_confidence >= 0.85`
- 人工修改率的 v1 判定固定为：
  - 若一次 review 对实体/关系做了 `>= 2` 处实质修改，或
  - 修改项占抽取项总数 `>= 30%`
  - 则该样本进入 `error set`
- `error case` 固定包含：
  - 原文
  - 原始结果
  - 冲突与评分
  - 人工修订结果
  - 修改摘要
  - 建议 few-shot 标签
  - 建议 prompt 优化点
- `graph memory` 固定包含：
  - `entities`
  - `aliases`
  - `relations`
  - `source_runs`
  - `last_updated`
- Web 应用数据流固定为：
  - 页面只读取 `data/` 下的 JSON 文件
  - skill/脚本负责写数据
  - 页面不直接执行抽取

## Web Panel
- 首页默认打开最近一次运行，并支持切换历史运行。
- 主布局采用三栏或二栏自适应：
  - 左侧为原文/chunk/证据
  - 中间为实体与关系主结果
  - 右侧为冲突、置信度、人工 review 和图谱增量摘要
- 核心交互固定为：
  - 点击实体高亮原文 span、关联关系、证据和图谱节点
  - 点击关系高亮 head/tail 与证据片段
  - 切换粒度视图
  - 过滤低置信、冲突项、已编辑项
  - 人工编辑实体类型、归一名、关系类型、关系方向
  - 保存 review 后写入修订版和错误集评估
- 可视化组件固定包含：
  - span overlay 高亮层
  - 关系边列表
  - 小型关系图谱视图
  - 置信度条/徽标
  - issue 卡片
  - run history 列表
- 不做花哨 3D 或重图形；重点是快速检阅、debug 和人工 review。

## Codex Integration
- 当前工程目录保留为主工作区，skill 目录放在当前目录子路径 `hierarchical-er-skill/`。
- 通过 Windows 目录链接把 `C:\Users\24045\.codex\skills\hierarchical-er-skill` 指向当前工程内的 `hierarchical-er-skill/`。
- `openai.yaml` 允许隐式调用，同时支持显式 `$hierarchical-er-skill`。
- README 中加入“如何在 Codex 中调用”演示：
  - `只要粗粒度，抽取这段文本的实体关系`
  - `输出业务可读的标准粒度`
  - `尽可能细，并保留证据`
- skill 每次运行后调用本地脚本刷新 `data/` 并打开 `webapp`，形成稳定产品闭环。

## Test Plan
- 粒度控制测试：同一文本在三档模式下输出层级正确，字段稳定。
- 中文别名测试：简称/全称/别名应归一到同一实体。
- 英文多关系测试：方向规则与允许配对必须正确。
- 局部跨句测试：只允许 schema 配置窗口内的跨句关系。
- 冲突修正测试：粗细粒度冲突、关系方向冲突、重复关系冲突必须被修正或显式进入 `issues`。
- 低置信度测试：混合评分应把证据不足或冲突结果打入低置信。
- 人工 review 测试：编辑后必须正确保存修订版、计算修改率、触发 error set 规则。
- graph memory 测试：多次运行后同实体跨文档归一稳定，关系增量不重复污染。
- Web 测试：最新运行、历史运行、实体高亮、关系高亮、冲突过滤、保存编辑都可用。
- 回归测试：修改 skill、schema、规则或 UI 数据契约后，黄金样本与页面加载都必须通过。
- 集成测试：Codex 通过 `$hierarchical-er-skill` 触发后，必须完成抽取、写数据、刷新面板、可打开查看。

## Assumptions
- v1 前端采用原生 HTML/CSS/JS，无 React/Vite 构建链。
- v1 图谱增量记忆使用本地 JSON，不上 SQLite。
- v1 自动持续迭代只做到“沉淀 + 推荐”，不自动重写 prompt，不自动修改 skill。
- v1 Web 面板默认浅色主题，保留后续深色模式接口，但不强制首版实现。
- v1 不接文件解析和批处理，只围绕纯文本输入与历史运行管理。
- 不加入任何静默兜底或模糊修补逻辑；所有不确定结果必须进入 `issues`、`error_capture` 或 review 流程。
