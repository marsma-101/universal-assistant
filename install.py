#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
install.py — universal-assistant 自安装脚本（零依赖，跨平台）。

职责单一：**把本技能复制到用户的技能根下，用正确的目录名**。
不扫描、不写入任何其它 agent 软件的数据。

用法：
    python install.py [--root <技能根>] [--agent claude-code|codex|opencode|hermes|dsh|workbuddy|auto]

确定目标技能根（优先级）：
    1. --root 显式指定
    2. 环境变量：DSH_HOME / CODEX_HOME / CLAUDE_CONFIG_DIR / HERMES_SKILL_DIR / OPENCLAW_HOME / WORKBUDDY_HOME
       （各 agent 把_home 指向其「技能根」即可；例如 Claude Code 指向 ~/.claude，
        WorkBuddy 指向 ~/.workbuddy/skills，DSH 指向其技能根）
    3. 仍无法确定 → 询问用户（不猜、不遍历写入）

目标路径 = <技能根>/universal-assistant

行为：
    - 若源目录名 != universal-assistant → 复制（保留源仓库，不移动）
    - 校验：目标 SKILL.md 存在 + frontmatter name == "universal-assistant" + description 非空
    - 打印结果与「请重启 agent 会话」提示（DSH 除外，有文件监听可即时生效）

解释器：python3 / python / py -3 均可。
"""
import os
import sys
import json
import shutil
import argparse

NAME = "universal-assistant"

# agent -> 用于推断技能根的环境变量（指向各自的「技能根目录」）
ENV_BY_AGENT = {
    "dsh": "DSH_HOME",
    "codex": "CODEX_HOME",
    "claude-code": "CLAUDE_CONFIG_DIR",
    "claude": "CLAUDE_CONFIG_DIR",
    "hermes": "HERMES_SKILL_DIR",
    "openclaw": "OPENCLAW_HOME",
    "opencode": "OPENCLAW_HOME",
    "workbuddy": "WORKBUDDY_HOME",
}


def here_dir():
    return os.path.dirname(os.path.abspath(__file__))


def is_valid_skill(skill_dir):
    """校验技能目录规范：name == 目录名且 description 非空。"""
    md = os.path.join(skill_dir, "SKILL.md")
    if not os.path.isfile(md):
        return False, "SKILL.md 不存在"
    name_ok = os.path.basename(skill_dir) == NAME
    desc_ok = False
    try:
        with open(md, encoding="utf-8") as f:
            text = f.read()
        in_fm = False
        for line in text.splitlines():
            if line.strip() == "---":
                in_fm = not in_fm
                continue
            if in_fm:
                if line.startswith("name:"):
                    v = line.split(":", 1)[1].strip()
                    name_ok = (v == NAME)
                if line.startswith("description:"):
                    desc_ok = bool(line.split(":", 1)[1].strip())
    except Exception as e:
        return False, "读取 SKILL.md 失败: %s" % e
    if not name_ok:
        return False, "frontmatter name 不等于 %s（当前目录名或 name 字段不符）" % NAME
    if not desc_ok:
        return False, "frontmatter description 为空"
    return True, ""


def resolve_root(args):
    if args.root:
        return args.root
    if args.agent and args.agent in ENV_BY_AGENT:
        v = os.environ.get(ENV_BY_AGENT[args.agent])
        if v:
            return v
    # 通用环境变量兜底
    for e in ("DSH_HOME", "CODEX_HOME", "CLAUDE_CONFIG_DIR",
              "HERMES_SKILL_DIR", "OPENCLAW_HOME", "WORKBUDDY_HOME"):
        if os.environ.get(e):
            return os.environ[e]
    # 仍无法确定 → 询问（不猜、不遍历）
    print("无法确定技能根目录。")
    print("请指定你的 AI agent 的「技能根目录」，例如：")
    print("  Claude Code : ~/.claude")
    print("  WorkBuddy   : ~/.workbuddy/skills")
    print("  DSH         : <DSH 技能根>")
    print("（该目录下的子目录 universal-assistant/ 将是安装目标）")
    try:
        ans = input("技能根目录绝对路径: ").strip()
    except EOFError:
        ans = ""
    if not ans:
        return None
    return os.path.expanduser(ans)


def main():
    parser = argparse.ArgumentParser(description="universal-assistant 自安装")
    parser.add_argument("--root", help="技能根目录（绝对路径）")
    parser.add_argument("--agent",
                        help="目标 agent 名（用于读环境变量推断技能根）："
                             "claude-code|codex|opencode|hermes|dsh|workbuddy|auto")
    args = parser.parse_args()

    src = here_dir()
    root = resolve_root(args)
    if not root:
        print("[失败] 未提供技能根目录，已取消安装。")
        sys.exit(2)

    dest = os.path.join(root, NAME)
    print("源目录 : %s" % src)
    print("目标目录: %s" % dest)

    if os.path.exists(dest):
        ok, msg = is_valid_skill(dest)
        if ok:
            print("[跳过] 目标已存在且合法：%s" % dest)
        else:
            print("[警告] 目标已存在但校验未通过：%s" % msg)
            print("         请手动删除 %s 后重试，或确认目录名与 name 一致。" % dest)
            sys.exit(3)
    else:
        try:
            shutil.copytree(src, dest)
        except Exception as e:
            print("[失败] 复制失败：%s" % e)
            sys.exit(4)
        ok, msg = is_valid_skill(dest)
        if not ok:
            print("[失败] 复制后校验未通过：%s" % msg)
            sys.exit(5)
        print("[成功] 已安装到 %s" % dest)

    print("")
    print("安装完成。请**重启你的 agent 会话**使技能生效")
    print("（DSH 有文件监听可即时生效，无需重启）。")
    print("首次激活时助理会请你给本助理起个名字。")


if __name__ == "__main__":
    main()
