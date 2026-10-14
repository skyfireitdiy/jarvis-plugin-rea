"""
rea_setup 工具：一键配置 REA（Reverse Engineer Anything）环境。

功能：
- 检测本机 Node.js / npm / npx 是否就绪
- 通过 npx 安装/运行 REA（rea-agents），验证 MCP server 可用
- 检查并输出 REA 环境配置结果，供 Agent 与用户确认

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


class ReaSetupTool:
    # 文件名必须与工具名一致，便于注册表自动加载
    name = "rea_setup"
    description = (
        "一键配置 REA（Reverse Engineer Anything）逆向工程环境："
        "检测 Node.js/npm/npx，安装并验证 rea-agents，"
        "确认 REA MCP 服务器可正常启动。"
    )
    parameters = {
        "type": "object",
        "properties": {
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

    def _run(self, cmd: list, timeout: int = 300) -> tuple:
        """运行命令并返回 (returncode, stdout, stderr)。"""
        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            return proc.returncode, proc.stdout, proc.stderr
        except subprocess.TimeoutExpired:
            return -1, "", f"命令超时（>{timeout}s）: {' '.join(cmd)}"
        except Exception as e:
            return -1, "", f"命令执行异常: {e}"

    def execute(self, args: Dict[str, Any]) -> Dict[str, Any]:
        try:
            version = args.get("version", "latest")
            verify_mcp = args.get("verify_mcp", True)
            lines: list = []
            errors: list = []

            # 1. 检测 Node.js 环境
            lines.append("=== 1. 检测 Node.js 环境 ===")
            for cmd_name in ("node", "npm", "npx"):
                path = shutil.which(cmd_name)
                if path:
                    rc, out, err = self._run([cmd_name, "--version"], timeout=30)
                    ver = out.strip() if rc == 0 else f"(获取版本失败: {err.strip()})"
                    lines.append(f"  ✅ {cmd_name}: {path} (v{ver})")
                else:
                    lines.append(f"  ❌ {cmd_name}: 未找到，请先安装 Node.js 22+")
                    errors.append(f"缺少 {cmd_name} 命令")

            if errors:
                lines.append("\n=== 结论：环境不完整 ===")
                lines.append(
                    "请先安装 Node.js 22.x（>=22.19）/ 24.x（>=24.11）/ 26+ 与 npm，"
                    "然后重新运行本工具。"
                )
                return {
                    "success": False,
                    "stdout": "\n".join(lines),
                    "stderr": "; ".join(errors),
                }

            # 2. 获取 REA 版本
            lines.append("\n=== 2. 获取 REA 版本 ===")
            rc, out, err = self._run(
                ["npx", "-y", f"rea-agents@{version}", "--version"], timeout=180
            )
            if rc == 0:
                lines.append(f"  ✅ rea-agents 可用: v{out.strip()}")
            else:
                lines.append(f"  ❌ 获取 rea-agents 版本失败: {err.strip()}")
                return {
                    "success": False,
                    "stdout": "\n".join(lines),
                    "stderr": f"rea-agents 安装/获取失败: {err.strip()}",
                }

            # 3. 验证 MCP 服务器（可选）
            if verify_mcp:
                lines.append("\n=== 3. 验证 REA MCP 服务器 ===")
                mcp_ok = self._verify_mcp(version)
                if mcp_ok:
                    lines.append("  ✅ REA MCP 服务器启动成功（stdio），工具列表可获取")
                else:
                    lines.append("  ❌ REA MCP 服务器启动验证失败")
                    errors.append("REA MCP 服务器启动验证失败")

            # 4. 汇总
            lines.append("\n=== 4. 配置结果 ===")
            if errors:
                lines.append("环境配置未完全就绪，请根据上方提示修复后重试。")
                return {
                    "success": False,
                    "stdout": "\n".join(lines),
                    "stderr": "; ".join(errors),
                }

            lines.append("✅ REA 环境配置完成！")
            lines.append(
                "REA MCP 服务器已由本插件自动注册（config.yaml 的 mcp 扩展点），"
                "重启 Jarvis 后即可使用 rea_* 逆向工具。"
            )
            lines.append(
                "提示：如需手动安装全局 CLI，可执行 `npm install --global rea-agents`。"
            )
            return {
                "success": True,
                "stdout": "\n".join(lines),
                "stderr": "",
            }
        except Exception as e:
            return {
                "success": False,
                "stdout": "",
                "stderr": f"rea_setup 执行异常: {e}",
            }

    def _verify_mcp(self, version: str) -> bool:
        """启动 REA MCP server 并做 initialize 握手，验证工具列表可获取。"""
        import json as _json

        proc = None
        try:
            proc = subprocess.Popen(
                ["npx", "-y", f"rea-agents@{version}", "mcp"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
            )
            init = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {"name": "jarvis-rea-plugin", "version": "1.0"},
                },
            }
            proc.stdin.write(_json.dumps(init) + "\n")
            proc.stdin.flush()
            line = proc.stdout.readline()
            if not line:
                return False
            resp = _json.loads(line)
            if "result" not in resp:
                return False
            # 发送 initialized 通知并请求工具列表
            proc.stdin.write(
                _json.dumps(
                    {"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}}
                )
                + "\n"
            )
            proc.stdin.write(
                _json.dumps({"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}})
                + "\n"
            )
            proc.stdin.flush()
            line = proc.stdout.readline()
            if not line:
                return False
            tools_resp = _json.loads(line)
            tools = tools_resp.get("result", {}).get("tools", [])
            return len(tools) > 0
        except Exception:
            return False
        finally:
            if proc:
                try:
                    proc.terminate()
                    proc.wait(timeout=5)
                except Exception:
                    try:
                        proc.kill()
                    except Exception:
                        pass
