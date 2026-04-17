# hierarchical-er-skill

`hierarchical-er-skill` 是一个面向实体关系抽取的完整 skill 工程，目标不是只输出一次性结果，而是把抽取、约束校验、混合置信度、跨文档图谱记忆、错误样本沉淀和本地 review 面板串成一个稳定闭环。

## 项目亮点

- 支持 `coarse`、`standard`、`fine` 三档粒度控制。
- 固定输出稳定 JSON 协议，便于回归和前端读取。
- 每次运行都能更新 `graph-memory.json`，做本地增量图谱记忆。
- 自动把低置信、规则冲突、人工大幅修订样本沉淀到 `error set`。
- 自带原生 HTML/CSS/JS 本地 Web 面板，用于审阅、debug 和人工 review。
- 只使用 Python 标准库与静态前端，无额外构建步骤。

## 目录结构

```text
.
├── PLAN.md
├── README.md
└── hierarchical-er-skill/
    ├── SKILL.md
    ├── agents/openai.yaml
    ├── schema/schema.yaml
    ├── contracts/
    ├── references/
    ├── scripts/
    ├── data/
    └── webapp/
```

## 核心运行流程

1. 让 Codex 按 skill 规则抽取实体与关系，并输出符合 `contracts/output.schema.json` 的 JSON。
2. 运行 `check_constraints.py` 检查方向、允许配对、重复关系和跨句窗口冲突。
3. 运行 `score_confidence.py` 计算混合置信度并标注低置信项。
4. 运行 `update_graph_memory.py` 更新 `data/graph/graph-memory.json`。
5. 运行 `capture_error_case.py` 把命中规则的样本沉淀到 `error set`。
6. 运行 `serve_review_app.py` 启动本地 review 面板并打开浏览器。

## 典型命令

```powershell
python hierarchical-er-skill/scripts/validate_output.py hierarchical-er-skill/data/runs/seed-run.json
python hierarchical-er-skill/scripts/check_constraints.py hierarchical-er-skill/data/runs/seed-run.json --write
python hierarchical-er-skill/scripts/score_confidence.py hierarchical-er-skill/data/runs/seed-run.json --write
python hierarchical-er-skill/scripts/update_graph_memory.py hierarchical-er-skill/data/runs/seed-run.json
python hierarchical-er-skill/scripts/capture_error_case.py hierarchical-er-skill/data/runs/seed-run.json
python hierarchical-er-skill/scripts/report_regression.py
python hierarchical-er-skill/scripts/serve_review_app.py --port 8765
```

## Codex 中如何调用

- `只要粗粒度，抽取这段文本的实体关系`
- `输出业务可读的标准粒度`
- `尽可能细，并保留证据`
- `用 $hierarchical-er-skill 审阅并记录这段文本的实体关系`

## Web 面板

面板默认打开最近一次运行，支持：

- 原文与 chunk 浏览
- 实体 span 高亮
- 关系与图谱摘要
- 置信度分层
- issue 列表
- 历史运行切换
- 人工 review 编辑并保存修订版
- graph memory 增量摘要
- error set 命中记录

## 数据闭环

- 运行结果写入 `data/runs/`
- 跨文档记忆写入 `data/graph/graph-memory.json`
- 错误样本索引写入 `data/errors/error-set.jsonl`
- 可回放案例包写入 `data/errors/cases/`
- 黄金样本放在 `data/regression/cases/`

## 设计边界

- v1 不做训练，也不自动重写 prompt。
- v1 不做静默兜底；不确定项必须进入 `issues`、`error_capture` 或 review。
- v1 只围绕纯文本输入，不处理文件解析和批处理。

