# rea — REA 逆向工程集成插件

> 基于 [REA（Reverse Engineer Anything）](https://github.com/morluto/rea) 的 Jarvis 外部插件。
> 让 Jarvis Agent 具备二进制 / 应用 / 运行时逆向分析能力，支持**一键环境配置**、**多节点批量部署**与 **MCP 自动注册**。

REA 是一个面向编码 Agent 的逆向工程工具包（npm 包 `rea-agents`），通过 MCP 服务器 + CLI
让 Agent 深入分析目标（原生二进制、JavaScript/Electron、.NET 程序集、Android APK、网站、进程行为等），
直到二进制级别，并提供结构化还原证据。分析全部在本地运行。

## 功能特性

| 功能 | 说明 |
| --- | --- |
| ⚙️ 一键环境配置 | `rea_setup` 工具：检测 Node 环境 → 拉取 rea-agents → 验证 MCP 服务器 |
| 🌐 多节点配置 | `rea_node_setup` 工具：通过网关在多个 Jarvis 节点批量部署 REA |
| 🔌 注册 MCP | 插件 `mcpserver` 扩展点自动注册 REA MCP（stdio: `npx rea-agents mcp`）；`rea_register_mcp` 工具可手动管理全局 mcp 配置 |
| 📋 使用规则 | `rules/rea.md` 指导 Agent 正确配置与使用 REA |

## 安装

### 从插件市场安装（推荐）

在 Jarvis 插件管理面板的「市场」页签搜索 `rea`，一键安装。

### 命令行安装

```bash
# 从源码仓库安装
jarvis --install-plugin https://github.com/skyfireitdiy/jarvis-plugin-rea

# 或从本地目录安装
jarvis --install-plugin /path/to/rea
```

安装后重启 Jarvis 使插件与 MCP 注册生效：

```bash
jarvis --list-plugins   # 确认 rea 插件已注册
```

## 使用

### 1. 一键配置环境

让 Agent 执行 `rea_setup` 工具，或直接说：

> 帮我配置 REA 逆向工程环境

工具会检测 Node.js / npm / npx，拉取 `rea-agents`，并验证 MCP 服务器可启动。

### 2. 多节点批量配置

让 Agent 执行 `rea_node_setup` 工具（可指定 `node_ids` 或对全部节点执行）：

> 在所有节点上部署 REA 环境

工具会列出网关节点，逐节点检测 Node 环境、验证 rea-agents 与 MCP 启动。

### 3. 注册 / 管理 MCP

REA MCP 已由插件自动注册。如需手动管理全局配置，用 `rea_register_mcp` 工具
检查/写入 `~/.jarvis/config.yaml` 的 `mcp` 列表。

注册后 REA 工具以 `rea_tool_call_<tool_name>` 形式提供（共 170+ 个工具），
例如 `rea_tool_call_inspect_native_load_image`、`rea_tool_call_procedure_pseudo_code` 等。

### 4. 使用 REA 进行逆向分析

安装并重启后，直接让 Agent 分析目标：

> 用 REA 分析 /path/to/app，解释它的搜索功能是怎么实现的，展示证据

## 插件结构

```
rea/
├── config.yaml          # 插件配置：mcpserver（MCP 注册）、rules、tools、dependencies
├── README.md
├── rules/
│   └── rea.md           # REA 使用规则（含配置文档）
└── tools/
    ├── rea_setup.py         # 一键环境配置
    ├── rea_node_setup.py    # 多节点批量配置
    └── rea_register_mcp.py  # 手动注册/管理 MCP
```

## 环境要求

- Jarvis（支持外部插件）
- Node.js 22.x（>=22.19）/ 24.x（>=24.11）/ 26+ 与 npm（REA 依赖）
- 深度原生二进制分析需用户已有的 Hopper / Ghidra / IDA（REA 不代为安装）

## 许可证

MIT
