"""
rea_node_setup 工具：多节点批量配置 REA（Reverse Engineer Anything）环境。

功能：
- 列出当前 Jarvis 网关的所有节点（list_nodes）
- 在指定节点（或全部节点）上通过 exec_command 一键部署 REA：
  检测 Node/npm/npx → 安装 rea-agents → 验证 MCP 可用
- 输出每个节点的配置结果汇总

返回:
- success (bool)
- stdout (str)
- stderr (str)
"""
import json
import shutil
import subprocess
from typing import Any
from typing import Dict
from typing import List


class ReaNodeSetupTool:
    # 文件名必须与工具名一致，便于注册表自动加载
    name = "rea_node_setup"
    description = (
        "多节点批量配置 REA（Reverse Engineer Anything）逆向工程环境："
        "列出 Jarvis 网关节点，在指定节点或全部节点上通过 exec_command "
        "一键检测 Node 环境、安装 rea-agents 并验证 MCP 服务器可用。"
    )
    parameters = {
        "type": "object",
        "properties": {
            "node_ids": {
                "type": "array",
                "items": {"type": "string"},
                "description": "目标节点 ID 列表；不传则对全部节点执行",
            },
            "version": {
                "type": "string",
                "description": "要安装的 rea-agents 版本（默认 latest）",
            },
            "verify_mcp": {
                "type": "boolean",
                "description": "是否验证 MCP 服务器可启动（默认 true）",
            },
        },
        "required": [],
    }

    @staticmethod
    def check() -> bool:
        """工具是否可用：需要 node/npm/npx 命令。"""
        return (
            shutil.which("node") is not None
            and shutil.which("npm") is not None
            and shutil.which("npx") is not None
        )

    def _list_nodes(self) -> List[Dict[str, Any]]:
        """通过 gateway 的 list_nodes 获取节点列表。"""
        try:
            from jarvis.jarvis_tools.gateway_manager import GatewayManagerTool

            tool = GatewayManagerTool()
            result = tool.execute({"action": "list_nodes"})
            if not result.get("success"):
                return []
            out = result.get("stdout", "")
            try:
                data = json.loads(out)
                if isinstance(data, list):
                    return data
                if isinstance(data, dict):
                    return data.get("nodes", data.get("data", []))
            except Exception:
                pass
            return []
        except Exception:
            return []

    def _exec_on_node(self, node_id: str, command: str, timeout: int = 300) -> str:
        """在指定节点上执行命令（exec_command），返回输出。"""
        try:
            from jarvis.jarvis_tools.gateway_manager import GatewayManagerTool

            tool = GatewayManagerTool()
            result = tool.execute(
                {
                    "action": "exec_command",
                    "node_id": node_id,
                    "command": command,
                    "timeout": timeout,
                }
            )
            if result.get("success"):
                return result.get("stdout", "")
            return f"❌ {result.get('stderr', '执行失败')}"
        except Exception as e:
            return f"❌ 节点执行异常: {e}"

    def execute(self, args: Dict[str, Any]) -> Dict[str, Any]:
        try:
            node_ids = args.get("node_ids") or []
            version = args.get("version", "latest")
            verify_mcp = args.get("verify_mcp", True)
            lines: list = []

            # 1. 获取节点列表
            lines.append("=== 1. 获取 Jarvis 网关节点 ===")
            nodes = self._list_nodes()
            if not nodes:
                lines.append("  ⚠️ 未获取到节点列表（可能当前无多节点环境或网关未启动）。")
                lines.append("  请确认已配置多节点（gateway）后重试。")
                return {
                    "success": False,
                    "stdout": "\n".join(lines),
                    "stderr": "无法获取节点列表",
                }

            for n in nodes:
                nid = n.get("node_id") or n.get("id") or n.get("name", "")
                host = n.get("hostname") or n.get("host", "")
                lines.append(f"  - {nid} ({host})")
            lines.append(f"  共 {len(nodes)} 个节点")

            # 2. 确定目标节点
            if node_ids:
                targets = [n for n in nodes if (n.get("node_id") or n.get("id") or n.get("name")) in node_ids]
                if not targets:
                    lines.append(f"\n  ⚠️ 指定的节点 {node_ids} 不在节点列表中")
                    return {
                        "success": False,
                        "stdout": "\n".join(lines),
                        "stderr": f"未找到指定节点: {node_ids}",
                    }
            else:
                targets = nodes
            lines.append(f"\n=== 2. 目标节点（{len(targets)} 个） ===")

            # 3. 逐节点部署 REA
            results: list = []
            for n in targets:
                nid = n.get("node_id") or n.get("id") or n.get("name", "")
                host = n.get("hostname") or n.get("host", "")
                lines.append(f"\n--- 部署到节点 {nid} ({host}) ---")

                # 3.1 检测 Node 环境
                check_cmd = (
                    "node --version 2>/dev/null && npm --version 2>/dev/null && "
                    "npx --version 2>/dev/null || echo 'NODE_MISSING'"
                )
                env_out = self._exec_on_node(nid, check_cmd, timeout=60)
                if "NODE_MISSING" in env_out or "command not found" in env_out:
                    lines.append("  ❌ 该节点缺少 Node.js/npm/npx，跳过部署")
                    results.append({"node": nid, "ok": False, "reason": "缺少 Node 环境"})
                    continue
                lines.append(f"  环境: {env_out.strip()[:200]}")

                # 3.2 验证 rea-agents 可用
                ver_cmd = f"npx -y rea-agents@{version} --version 2>&1 | tail -1"
                ver_out = self._exec_on_node(nid, ver_cmd, timeout=300)
                lines.append(f"  rea-agents: {ver_out.strip()[:200]}")

                # 3.3 验证 MCP（可选）
                mcp_ok = True
                if verify_mcp:
                    # 通过 node 脚本做 MCP initialize 握手（避免依赖额外工具）
                    mcp_script = (
                        "node -e \""
                        "const {spawn}=require('child_process');"
                        "const p=spawn('npx',['-y','rea-agents@%s','mcp'],{stdio:['pipe','pipe','pipe']});"
                        "let out='';p.stdout.on('data',d=>out+=d);"
                        "p.stdin.write(JSON.stringify({jsonrpc:'2.0',id:1,method:'initialize',"
                        "params:{protocolVersion:'2024-11-05',capabilities:{},"
                        "clientInfo:{name:'jarvis-rea',version:'1.0'}}})+'\n');"
                        "setTimeout(()=>{console.log(out.includes('\\\"result\\\"')?'MCP_OK':'MCP_FAIL');"
                        "p.kill();process.exit(0);},30000);"
                        "\""
                    ) % version
                    mcp_out = self._exec_on_node(nid, mcp_script, timeout=120)
                    mcp_ok = "MCP_OK" in mcp_out
                    lines.append(
                        f"  MCP 验证: {'✅ 启动成功' if mcp_ok else '❌ 启动失败'}"
                    )

                results.append(
                    {
                        "node": nid,
                        "ok": mcp_ok,
                        "version": version,
                        "mcp_verified": mcp_ok,
                    }
                )

            # 4. 汇总
            lines.append("\n=== 3. 部署结果汇总 ===")
            ok_count = sum(1 for r in results if r["ok"])
            for r in results:
                status = "✅" if r["ok"] else "❌"
                lines.append(f"  {status} {r['node']}: {r.get('reason', '部署成功')}")
            lines.append(f"\n成功 {ok_count}/{len(results)} 个节点")

            if ok_count == len(results) and results:
                lines.append(
                    "\n✅ 全部节点 REA 环境配置完成！"
                    "各节点重启 Jarvis 后，rea MCP 服务器将自动注册。"
                )
                return {"success": True, "stdout": "\n".join(lines), "stderr": ""}
            else:
                lines.append("\n部分节点部署失败，请检查上方输出后重试。")
                return {
                    "success": False,
                    "stdout": "\n".join(lines),
                    "stderr": f"有 {len(results) - ok_count} 个节点部署失败",
                }
        except Exception as e:
            return {
                "success": False,
                "stdout": "",
                "stderr": f"rea_node_setup 执行异常: {e}",
            }
