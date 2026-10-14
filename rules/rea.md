---
name: rea_rule
description: 当需要配置 REA（Reverse Engineer Anything）逆向工程环境、注册 REA MCP、在多个节点部署 REA、或使用 REA 进行逆向分析时触发。触发词：REA、rea 工具、逆向工程、二进制分析、MCP 注册、环境配置、多节点部署。
---
# REA 插件使用规则

REA（Reverse Engineer Anything）是一个面向编码 Agent 的逆向工程工具包（npm 包 `rea-agents`），
通过 MCP 服务器 + CLI 让 Agent 深入分析二进制、应用与运行时行为，直到二进制级别，并提供结构化还原证据。

本插件将 REA 集成到 Jarvis，提供一键环境配置、多节点部署与 MCP 自动注册。

## 1. 一键环境配置（rea_setup）

使用 `rea_setup` 工具可一键完成 REA 环境配置：

1. **检测 Node.js 环境**：确认 `node`/`npm`/`npx` 已安装（REA 需要 Node.js 22.x（>=22.19）/ 24.x（>=24.11）/ 26+ 与 npm）。
2. **获取 rea-agents**：通过 `npx -y rea-agents@latest` 拉取并运行 REA（无需全局安装）。
3. **验证 MCP 服务器**：启动 `npx rea-agents mcp` 做 initialize 握手，确认工具列表可获取。

配置完成后，REA MCP 服务器已由插件 config.yaml 的 `mcp` 扩展点自动注册，
重启 Jarvis 后即可使用 `rea_tool_call_*` 逆向工具。

## 2. 多节点配置（rea_node_setup）

使用 `rea_node_setup` 工具可批量配置多个 Jarvis 节点：

1. 工具自动调用网关 `list_nodes` 获取节点列表。
2. 可指定 `node_ids` 或对全部节点执行。
3. 每个节点依次：检测 Node 环境 → 验证 rea-agents → 验证 MCP 启动。
4. 输出各节点部署结果汇总。

> 注意：多节点部署依赖 Jarvis 网关（gateway）已配置多节点环境；单节点环境会提示无法获取节点列表。

## 3. 指令模板（按目标安装配套工具）

插件通过 `replace_map` 提供指令模板，用户在输入框输入 `<rea.setup>` 或 `<rea.doctor>` 即触发：

- **`<rea.setup>`**：一键配置引导。Agent 必须**先询问用户的逆向目标**，再**只安装该目标所需配套工具**：
  - **原生二进制/库** → Ghidra（+JDK 21+）/ Hopper（macOS/Linux）/ IDA
  - **JavaScript/Electron、.NET、Flutter、进程行为** → 仅需 Node.js + npm（REA 自带能力，无需额外工具）
  - **网站/浏览器** → Chrome / Chromium / Edge
  - **Android APK** → JADX + JDK 17+；看资源/清单加 Apktool+Java；连真机加 adb
  - **固件**（Linux）→ Binwalk 与/或 Unblob
  - **WASM** → WABT；**ELF/Linux crash** → pwntools/GDB/pwndbg；**PCAP**（Linux）→ TShark/capinfos
  - 安装前须向用户确认方案，禁止未经确认擅自安装系统级软件；已安装的跳过。
  - 验证：`npx -y rea-agents@latest doctor --provider <provider> --json`（ghidra/hopper/ida/jadx/chrome/binwalk 等）。
- **`<rea.doctor>`**：诊断 REA 环境，检查 Node、rea-agents、MCP 与各 provider 就绪状态。

> 原则：**只装用户逆向目标所需的工具**，不盲目安装全部配套工具。

## 4. 注册 MCP

REA MCP 通过插件 `mcp` 扩展点自动注册（stdio: `npx rea-agents mcp`），无需手动配置全局 `~/.jarvis/config.yaml`。

MCP 工具命名：注册后工具以 `rea_tool_call_<tool_name>` 形式出现（`.` 替换为 `_`）。

## 5. 使用 REA 进行逆向分析

安装并重启后，Agent 可通过 REA MCP 工具（`rea_tool_call_*`）进行逆向分析：

- **原生二进制**：伪代码、汇编、字符串、符号、调用与引用（需 Hopper/Ghidra/IDA）。
- **JavaScript/Electron**：模块、导入、源码映射、路由、IPC 关系（无需原生分析引擎）。
- **.NET 程序集**：元数据、CIL 指令、依赖关系（静态分析）。
- **Android APK**：清单声明、类、反编译方法（需 headless JADX + JDK）。
- **网站**：页面结构、脚本、网络观察、截图（需 Chrome 系浏览器）。
- **进程行为**：终端输出、交互、退出与文件系统观察（Linux/macOS）。

**使用原则**：
- 只分析你有权检查的目标（合法研究/教育/互操作/软件保留）。
- 分析在本地运行，结果含证据与局限说明。
- 深度的原生分析需用户已有的 Hopper/Ghidra/IDA，REA 不代为安装。

## 6. 故障排查

| 现象 | 排查 |
| --- | --- |
| `rea_setup` 报缺少 node/npm/npx | 安装 Node.js 22+ 后重试 |
| MCP 启动验证失败 | 检查网络能否访问 npm registry；`npx rea-agents@latest --version` 手动验证 |
| 工具以 `rea_tool_call_*` 未出现 | 重启 Jarvis 使 mcp 扩展点生效；检查启动日志 MCP 注册警告 |
| 多节点部署失败 | 确认网关节点在线、节点有 Node 环境与网络 |
| `<rea.setup>` 未生效 | 确认输入 `<rea.setup>`（含尖括号）；检查插件 config.yaml 的 replace_map 已加载 |
| 配套工具验证失败 | 用 `npx -y rea-agents@latest doctor --provider <provider> --json` 查看具体缺失项 |
