"""
rea 工具模板。

用途:
- 在此描述工具的用途与行为。

参数:
- 在此描述参数。

返回:
- success (bool)
- stdout (str)
- stderr (str)
"""
import json
from typing import Any
from typing import Dict


class ReaTool:
    # 文件名必须与工具名一致，便于注册表自动加载
    name = "rea_tool"
    description = "rea 工具：请补充工具描述。"

    parameters = {
        "type": "object",
        "properties": {
            "input": {
                "type": "string",
                "description": "输入内容",
            },
        },
        "required": ["input"],
    }

    @staticmethod
    def check() -> bool:
        """工具是否可用（无外部依赖时始终返回 True）。"""
        return True

    def execute(self, args: Dict[str, Any]) -> Dict[str, Any]:
        try:
            data = args.get("input")
            if not data or not isinstance(data, str):
                return {
                    "success": False,
                    "stdout": "",
                    "stderr": "参数错误：input 必须是非空字符串",
                }
            output = {
                "echo": data,
                "note": "请在此实现实际逻辑",
            }
            return {
                "success": True,
                "stdout": json.dumps(output, ensure_ascii=False, indent=2),
                "stderr": "",
            }
        except Exception as e:
            return {
                "success": False,
                "stdout": "",
                "stderr": f"rea_tool 执行异常: {e}",
            }
