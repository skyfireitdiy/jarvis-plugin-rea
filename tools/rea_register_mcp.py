"""
rea_register_mcp 工具：手动注册 REA MCP 服务器到 Jarvis 配置。

功能：
- 检查 ~/.jarvis/config.yaml 中是否已存在 rea MCP 配置
- 若不存在，将 REA MCP（stdio: npx rea-agents mcp）写入 mcp 列表
- 若已存在，可更新 enable 状态或跳过
- 输出当前 mcp 配置状态

返回:
- success (bool)
- stdout (str)
- stderr (str)
"""
import json
import os
from pathlib import Path
from typing import Any
from typing import Dict
from typing import List


class ReaRegisterMcpTool:
    # 文件名必须与工具名一致，便于注册表自动加载
    name = "rea_register_mcp"
    description = (
        "注册 REA（Reverse Engineer Anything）MCP 服务器到 Jarvis 配置："
        "检查/写入 ~/.jarvis/config.yaml 的 mcp 列表，"
        "配置 stdio 类型的 rea MCP 服务器（npx rea-agents mcp）。"
    )
    parameters = {
        "type": "object",
        "properties": {
            "enable": {
                "type": "boolean",
                "description": "是否启用该 MCP（默认 true；false 时写入 enable: false 或移除）",
            },
            "force": {
                "type": "boolean",
                "description": "是否强制覆盖已有 rea MCP 配置（默认 false，已存在则跳过）",
            },
        },
        "required": [],
    }

    @staticmethod
    def check() -> bool:
        """工具是否可用：始终可用。"""
        return True

    def _config_path(self) -> Path:
        """返回 Jarvis 配置文件路径。"""
        env = os.environ.get("JARVIS_CONFIG")
        if env and os.path.exists(env):
            return Path(env)
        return Path.home() / ".jarvis" / "config.yaml"

    def _rea_mcp_entry(self, enable: bool) -> Dict[str, Any]:
        """构造 REA MCP 配置项。"""
        return {
            "type": "stdio",
            "name": "rea",
            "command": "npx",
            "args": ["-y", "rea-agents@latest", "mcp"],
            "enable": enable,
        }

    def execute(self, args: Dict[str, Any]) -> Dict[str, Any]:
        try:
            enable = args.get("enable", True)
            force = args.get("force", False)
            config_path = self._config_path()
            lines: list = []

            lines.append(f"=== REA MCP 注册工具 ===")
            lines.append(f"配置文件: {config_path}")

            if not config_path.exists():
                return {
                    "success": False,
                    "stdout": "\n".join(lines),
                    "stderr": f"配置文件不存在: {config_path}",
                }

            import yaml

            with open(config_path, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f) or {}

            mcp_list: List[Dict[str, Any]] = config.get("mcp", []) or []
            if not isinstance(mcp_list, list):
                mcp_list = []

            # 查找已有 rea 配置
            existing_idx = None
            for i, item in enumerate(mcp_list):
                if isinstance(item, dict) and item.get("name") == "rea":
                    existing_idx = i
                    break

            new_entry = self._rea_mcp_entry(enable)

            if existing_idx is not None:
                existing = mcp_list[existing_idx]
                if not force:
                    lines.append("\n已存在 rea MCP 配置：")
                    lines.append(f"  {json.dumps(existing, ensure_ascii=False)}")
                    lines.append("\n无需重复注册（如需覆盖请传 force=true）。")
                    return {
                        "success": True,
                        "stdout": "\n".join(lines),
                        "stderr": "",
                    }
                # 覆盖
                mcp_list[existing_idx] = new_entry
                lines.append(f"\n已覆盖 rea MCP 配置: {json.dumps(new_entry, ensure_ascii=False)}")
            else:
                mcp_list.append(new_entry)
                lines.append(f"\n已新增 rea MCP 配置: {json.dumps(new_entry, ensure_ascii=False)}")

            config["mcp"] = mcp_list

            # 写回（保留注释需谨慎，这里用 yaml 重新序列化）
            with open(config_path, "w", encoding="utf-8") as f:
                yaml.safe_dump(config, f, allow_unicode=True, sort_keys=False)

            lines.append("\n✅ 已写入配置文件。请重启 Jarvis 使 MCP 注册生效。")
            lines.append("重启后 rea MCP 工具将以 rea_tool_call_* 形式注册。")
            return {"success": True, "stdout": "\n".join(lines), "stderr": ""}
        except Exception as e:
            return {
                "success": False,
                "stdout": "",
                "stderr": f"rea_register_mcp 执行异常: {e}",
            }
