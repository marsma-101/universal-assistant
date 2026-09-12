#!/usr/bin/env bash
# post-download-check.sh — 下载/解压后校验目录名（防 ZIP 静默失效）
#
# 用法：在技能目录内执行
#   bash post-download-check.sh
#
# 背景：GitHub「Download ZIP」解压后得到 universal-assistant-main/（多 -main 后缀）。
# 而 Agent Skills 规范硬性要求 目录名 == 技能 name（universal-assistant）。
# 不符时规范型 agent 会【静默跳过】整个技能——不报错、看似装好实则从未加载。
# 本脚本检测此情况，能自动修复就修复，否则给出明确命令。
set -u

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PARENT="$(dirname "$HERE")"
DIR="$(basename "$HERE")"
EXPECT="universal-assistant"
TARGET="$PARENT/$EXPECT"

if [ "$DIR" = "$EXPECT" ]; then
  echo "[OK] 目录名正确：$DIR —— agent 可正常加载本技能。"
  exit 0
fi

echo "[错误] 当前目录名是 '$DIR'，但 Agent Skills 规范要求 == '$EXPECT'。"
echo "       常见原因：用 GitHub「Download ZIP」解压得到带 -main 后缀的目录。"
echo "       后果：规范型 agent 会【静默跳过】整个技能（不报错、看似装好实从未加载）。"

# 自动修复：典型 -main 命名且目标不存在。
# 注意：须先离开当前目录再 rename（Windows/Git Bash 下不能重命名自身 cwd）。
if [ "$DIR" = "$EXPECT-main" ] && [ ! -e "$TARGET" ]; then
  if cd "$PARENT" 2>/dev/null && mv "$DIR" "$EXPECT" 2>/dev/null; then
    echo "[已修复] 已重命名为：$TARGET"
    echo "         请重启 agent 会话使技能生效。"
    exit 0
  fi
  # 回退到 HERE 继续给手动命令
  cd "$HERE" 2>/dev/null || true
fi

echo "       手动修复（任选其一）："
echo "         mv \"$HERE\" \"$TARGET\""
echo "       或重新克隆（目录名自动正确）："
echo "         git clone https://github.com/marsma-101/universal-assistant.git \"$TARGET\""
exit 1
