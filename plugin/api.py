"""
rea 插件私有功能层（运行在 gateway，供前端代理调用；不暴露给 Agent）。

本模块不声明在 tool_load_dirs，因此不会被 ToolRegistry 加载，Agent 看不到、调不到；
gateway 通过插件功能代理端点（POST /api/plugins/{node_id}/function-call）动态加载并调用。

约定：
- 每个功能是纯函数，返回 dict：{"success": bool, "data": .../ "message": .../ "error": ...}。
- 模块末尾定义 PUBLIC_FUNCTIONS 白名单，gateway 只允许调用白名单内函数。
"""
from typing import Any
from typing import Dict


def rea_echo(text: str = "") -> Dict[str, Any]:
    """示例功能：回显输入文本。请在此实现实际业务逻辑。"""
    if not text:
        return {"success": False, "error": "参数错误：text 不能为空"}
    return {"success": True, "data": {"echo": text}}


# gateway 只允许调用白名单内的功能（防任意函数被调用）
PUBLIC_FUNCTIONS: list[str] = ["rea_echo"]
