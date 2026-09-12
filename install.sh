#!/usr/bin/env bash
# install.sh — universal-assistant 一键安装（bash，跨平台）
#
# 用法：
#   bash install.sh <技能根目录>     例： bash install.sh ~/.workbuddy/skills
#   bash install.sh                   仅打印用法与各 agent 技能根示例
#
# 行为：
#   1. 把仓库克隆到 <技能根>/universal-assistant（目录名自动正确，避免 ZIP -main 陷阱）
#   2. 运行自带安装器 install.py —— 处理女娲决策树、运行安装自检、汇报
# 说明：本脚本只复制本技能自身，不碰任何其它软件数据；女娲为可选依赖，缺失不阻断。
set -u

REPO="https://github.com/marsma-101/universal-assistant.git"
NAME="universal-assistant"

# 选 python 解释器
if command -v python3 >/dev/null 2>&1; then PY="python3"
elif command -v python >/dev/null 2>&1; then PY="python"
elif command -v py >/dev/null 2>&1; then PY="py -3"
else PY="python"; fi

ROOT="${1:-}"

if [ -z "$ROOT" ]; then
  echo "用法: bash install.sh <技能根目录>"
  echo "示例:"
  echo "  bash install.sh ~/.workbuddy/skills   # WorkBuddy"
  echo "  bash install.sh ~/.claude             # Claude Code"
  echo "  bash install.sh ~/.codex              # Codex"
  echo ""
  echo "不传参数则只打印以上帮助。也可用自带安装器："
  echo "  python install.py --root <技能根>"
  exit 2
fi

# 展开 ~ 与变量
ROOT="$(eval echo "$ROOT")"
DEST="$ROOT/$NAME"

mkdir -p "$ROOT" 2>/dev/null || { echo "[失败] 无法创建技能根：$ROOT"; exit 3; }

if [ -d "$DEST" ]; then
  echo "[跳过] 已存在：$DEST"
else
  echo "克隆到（目录名已自动正确）：$DEST"
  if ! git clone "$REPO" "$DEST" 2>&1 | tail -5; then
    echo "[失败] 克隆失败，请检查 git/网络，或手动："
    echo "  git clone $REPO \"$DEST\""
    exit 1
  fi
fi

echo "运行自安装器（女娲决策树 + 安装自检）..."
if "$PY" "$DEST/install.py" --root "$ROOT"; then
  echo "安装完成。请重启 agent 会话使技能生效（DSH 有文件监听可即时生效）。"
else
  echo "[提示] 安装器返回非零（可能处于非交互环境）。可改跑："
  echo "  $PY \"$DEST/install.py\" --root \"$ROOT\" --no-nvwa"
fi
