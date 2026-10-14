#!/usr/bin/env bash
# ============================================================================
# rea 插件 pre-install 生命周期钩子
#
# 功能：
#   1. 检查 node / npm / npx 是否就绪；缺失时尝试自动安装（apt/brew）
#   2. 验证 Node 版本满足 REA 要求（22.x>=22.19 / 24.x>=24.11 / 26+）
#   3. 检查 rea-agents 是否已安装；未安装则全局安装（npm install -g），
#      失败时回退 npx 预热（插件 mcp 扩展点即用 npx 方式运行）
#
# 由 Jarvis 插件生命周期钩子在插件安装前以插件目录为工作目录执行。
# pre-* 钩子失败会中止安装（避免半成品状态），因此本脚本失败时返回非 0。
# ============================================================================
set -u

echo "=================================================="
echo " [rea pre-install] 检查并安装 Node.js 与 rea-agents"
echo "=================================================="

# ---------- 1. 检查 / 安装 Node.js ----------
echo ""
echo ">>> [1/3] 检查 Node.js / npm / npx"
NEED_NODE=0
for cmd in node npm npx; do
  if command -v "$cmd" >/dev/null 2>&1; then
    echo "  [OK] $cmd -> $(command -v "$cmd")"
  else
    echo "  [MISS] $cmd: 未找到"
    NEED_NODE=1
  fi
done

if [ "$NEED_NODE" = "1" ]; then
  echo ""
  echo ">>> 尝试自动安装 Node.js（apt/brew）"
  if command -v apt-get >/dev/null 2>&1; then
    if [ "$(id -u)" = "0" ]; then
      apt-get update -y >/dev/null 2>&1 && apt-get install -y nodejs npm >/dev/null 2>&1
    elif command -v sudo >/dev/null 2>&1; then
      sudo apt-get update -y >/dev/null 2>&1 && sudo apt-get install -y nodejs npm >/dev/null 2>&1
    else
      echo "  [FAIL] 需要 root 权限安装 node，请手动执行: sudo apt-get install -y nodejs npm"
      exit 1
    fi
  elif command -v brew >/dev/null 2>&1; then
    brew install node >/dev/null 2>&1
  else
    echo "  [FAIL] 无法自动安装 Node.js（无 apt/brew）。请手动安装 Node.js 22+ 后重试。"
    exit 1
  fi
  # 重新检查
  for cmd in node npm npx; do
    if ! command -v "$cmd" >/dev/null 2>&1; then
      echo "  [FAIL] $cmd 安装后仍不可用"
      exit 1
    fi
  done
  echo "  [OK] Node.js 安装完成"
fi

# ---------- 2. 验证 Node 版本 ----------
echo ""
echo ">>> [2/3] 验证 Node 版本（REA 需要 22.x>=22.19 / 24.x>=24.11 / 26+）"
NODE_VER=$(node --version 2>/dev/null | sed 's/^v//')
echo "  node: $NODE_VER"
MAJOR=$(echo "$NODE_VER" | cut -d. -f1)
MINOR=$(echo "$NODE_VER" | cut -d. -f2)
VER_OK=0
if [ "$MAJOR" -ge 26 ]; then
  VER_OK=1
elif [ "$MAJOR" = "24" ] && [ "$MINOR" -ge 11 ]; then
  VER_OK=1
elif [ "$MAJOR" = "22" ] && [ "$MINOR" -ge 19 ]; then
  VER_OK=1
elif [ "$MAJOR" = "23" ] || [ "$MAJOR" = "25" ]; then
  VER_OK=1
fi
if [ "$VER_OK" != "1" ]; then
  echo "  [FAIL] Node 版本过低（$NODE_VER），REA 需要 Node 22.19+ / 24.11+ / 26+"
  exit 1
fi
echo "  [OK] Node 版本满足 REA 要求"

# ---------- 3. 检查 / 安装 rea-agents ----------
echo ""
echo ">>> [3/3] 检查 rea-agents"
if command -v rea-agents >/dev/null 2>&1; then
  REA_VER=$(rea-agents --version 2>/dev/null || echo "?")
  echo "  [OK] rea-agents 已全局安装: v$REA_VER"
else
  echo "  rea-agents 未全局安装，尝试安装..."
  if npm install --global rea-agents >/dev/null 2>&1; then
    REA_VER=$(rea-agents --version 2>/dev/null || echo "?")
    echo "  [OK] rea-agents 已全局安装: v$REA_VER"
  else
    echo "  [WARN] 全局安装失败（可能无 npm 全局写权限），回退 npx 预热..."
    if npx -y rea-agents@latest --version >/dev/null 2>&1; then
      echo "  [OK] rea-agents 可通过 npx 使用: v$(npx -y rea-agents@latest --version 2>/dev/null)"
    else
      echo "  [FAIL] rea-agents 安装失败（全局与 npx 均不可用），请检查网络 / npm registry"
      exit 1
    fi
  fi
fi

echo ""
echo "=================================================="
echo " [rea pre-install] 完成：Node.js 与 rea-agents 就绪"
echo "=================================================="
exit 0
