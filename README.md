# rea

> 由 `jarvis --new-plugin rea` 生成的插件脚手架。

## 插件结构

```
rea/
├── config.yaml          # 插件配置（name/version + 扩展点声明）
├── README.md
├── rules/               # 规则（YAML front matter: name/description）
├── tools/               # 工具（class XxxTool, name==文件名 stem）
├── agents/              # Agent 定义（可选）
├── orchestration/       # 编排流水线（可选）
├── frontend/            # 前端扩展（可选，用 window.Vue）
└── plugin/              # 插件私有功能（可选，运行在 gateway，不暴露给 Agent）
```

## 开发指南

### 1. 工具（tools/）

工具文件是 Python 模块，类名 `ReaTool`，**`name` 必须等于文件名 stem（`rea_tool`）**，
否则注册表不会加载。实现 `check()`（静态方法，返回 bool 表示是否可用）与
`execute(args) -> {"success", "stdout", "stderr"}`。

### 2. 规则（rules/）

Markdown 文件，开头带 YAML front matter：

```yaml
---
name: <规则名>
description: <何时触发该规则>
---
```

### 3. 前端扩展（frontend/，可选）

前端 JS 是纯浏览器 ES module：**用 `window.Vue` 渲染，导出 default 组件，不要 `import 'vue'`**。
在 config.yaml 的 `frontend` 字段声明 `admin_tabs` / `sidebar_views` / `tool_panels`。

### 4. 编排（orchestration/，可选）

YAML 编排流水线，配合 `OrganizeAgents` 与 `jca -n --task-file` 消费。

### 5. 插件私有功能（plugin/，可选）

插件自己使用的功能实现（如 API 封装、业务纯函数）放在 `plugin/api.py`。
**不声明在 `tool_load_dirs`**，因此不会被 ToolRegistry 加载，Agent 看不到、调不到；
运行在 gateway，供前端代理调用。约定：

- 每个功能是纯函数，返回 dict：`{"success": bool, "data": .../ "message": .../ "error": ...}`。
- 模块末尾定义 `PUBLIC_FUNCTIONS: list[str]` 白名单，gateway 只允许调用白名单内函数。
- 前端通过 `POST /api/plugins/{node_id}/function-call` 调用（请求体 `{plugin, function, arguments}`）。

## 安装

```bash
jarvis --install-plugin rea
```

## 卸载

```bash
jarvis --uninstall-plugin rea
```
