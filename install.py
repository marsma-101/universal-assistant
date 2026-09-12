#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
install.py — universal-assistant 自安装脚本（零依赖，跨平台）。

职责：
  1. 把本技能复制到用户的「技能根」/<NAME>（保留源仓库，不移动）。
  2. 校验目录名 / name / description 规范。
  3. 处理可选依赖「女娲（nvwa）」——关键：nvwa 的任意回答都**不会中止**
     universal-assistant 的安装；universal-assistant 永远先装好。

女娲处理决策树（仅在用户技能根没有 huashu-nvwa 时触发）：
  Q1 是否现在安装原版女娲（huashu-nvwa）？
    是 → 安装原版（tools/install-nvwa.py），完成。
    否（拒绝）→ 不中止 UA 安装，继续：
        Q2 检测到疑似 nvwa 类技能 [候选]？用它代替原版来调用？
          是 → 写入 config.nvwa_invoke = 该技能目录名，完成。
          否 → Q3 那是否需要安装原版女娲？
              是 → 安装原版。
              否 → 完成 UA 安装，标记 nvwa_deferred（下次需要蒸馏专家时再问）。
  （非交互 / EOF 一律按「否 → 继续」处理，绝不中止。）

用法：
    python install.py [--root <技能根>] [--agent ...] [--no-nvwa]
    --no-nvwa：跳过女娲问答，直接进入「下次再问」状态（适合自动化 / 无终端）。
"""
import os
import sys
import json
import shutil
import argparse
import subprocess

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


def parse_name(md_path):
    """从 SKILL.md 抽取 frontmatter 的 name 字段。"""
    try:
        with open(md_path, encoding="utf-8") as f:
            text = f.read()
    except Exception:
        return None
    in_fm = False
    for line in text.splitlines():
        if line.strip() == "---":
            in_fm = not in_fm
            continue
        if in_fm and line.startswith("name:"):
            return line.split(":", 1)[1].strip().strip('"').strip("'")
    return None


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
    for e in ("DSH_HOME", "CODEX_HOME", "CLAUDE_CONFIG_DIR",
              "HERMES_SKILL_DIR", "OPENCLAW_HOME", "WORKBUDDY_HOME"):
        if os.environ.get(e):
            return os.environ[e]
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


# ---------- config（runtime: ~/.universal-assistant/config.json 优先）----------

def _config_paths(root):
    runtime = os.path.expanduser("~/.universal-assistant/config.json")
    skill = os.path.join(root, NAME, "config.json")
    return [p for p in (runtime, skill) if os.path.isfile(p)]


def read_config(root):
    for p in _config_paths(root):
        try:
            with open(p, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def write_config(root, data):
    runtime = os.path.expanduser("~/.universal-assistant/config.json")
    skill = os.path.join(root, NAME, "config.json")
    for p in (runtime, skill):
        d = os.path.dirname(p)
        try:
            os.makedirs(d, exist_ok=True)
            with open(p, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return p
        except Exception:
            continue
    return None


# ---------- 交互与女娲决策树 ----------

def yes_no(ask, prompt, default=False):
    try:
        a = ask(prompt).strip().lower()
    except EOFError:
        return default
    if not a:
        return default
    return a in ("y", "yes", "是", "t", "true", "1")


def detect_suspected_nvwa(root):
    """扫描技能根，找名字 / name 字段像 nvwa、但不是 huashu-nvwa 的目录。"""
    cands = []
    if not os.path.isdir(root):
        return cands
    for name in sorted(os.listdir(root)):
        d = os.path.join(root, name)
        if not os.path.isdir(d) or name == NAME:
            continue
        if name == "huashu-nvwa":
            continue
        low = name.lower()
        hit = ("nvwa" in low) or ("nuwa" in low) or ("女娲" in name)
        if not hit:
            md = os.path.join(d, "SKILL.md")
            if os.path.isfile(md):
                nm = parse_name(md)
                if nm and (("nvwa" in nm.lower()) or ("nuwa" in nm.lower()) or ("女娲" in nm)):
                    hit = True
        if hit:
            cands.append(name)
    return cands


def install_original(root):
    """调用 tools/install-nvwa.py 安装原版女娲；失败则给出手动命令。"""
    script = os.path.join(here_dir(), "tools", "install-nvwa.py")
    if os.path.isfile(script):
        try:
            subprocess.run([sys.executable, script, "--root", root], check=False)
            return True
        except Exception as e:
            print("[nvwa] 调用安装脚本失败：%s" % e)
            return False
    print("[nvwa] 未找到 tools/install-nvwa.py，请手动执行：")
    print("        git clone https://github.com/marsma-101/nuwa-skill.git %s"
          % os.path.join(root, "huashu-nvwa"))
    return False


def handle_nvwa(root, ask=input):
    canon = os.path.join(root, "huashu-nvwa")
    if os.path.isdir(canon) and is_valid_skill(canon):
        print("[nvwa] 已就绪：%s" % canon)
        cfg = read_config(root)
        if cfg.get("nvwa_invoke") in (None, "", "huashu-nvwa"):
            cfg["nvwa_invoke"] = "huashu-nvwa"
            write_config(root, cfg)
        return

    print("[nvwa] 未安装（可选增强：按需蒸馏领域专家才需要，不影响通用信息调研）")

    # Q1：是否现在安装原版
    if yes_no(ask, "是否现在安装原版女娲（huashu-nvwa）？[y/N] "):
        install_original(root)
        return

    # 用户拒绝安装 → 不中止 UA 安装，继续，主动问替代技能
    cands = detect_suspected_nvwa(root)
    if cands:
        print("[nvwa] 检测到疑似 nvwa 类技能：%s" % "、".join(cands))
        if yes_no(ask, "用现有技能「%s」代替原版来调用？[y/N] " % "/".join(cands)):
            chosen = cands[0]
            cfg = read_config(root)
            cfg["nvwa_invoke"] = chosen
            cfg.pop("nvwa_deferred", None)
            wp = write_config(root, cfg)
            print("[nvwa] 已设为用现有「%s」调用（写入 %s）" % (chosen, wp))
            return

    # Q3：那是否需要安装原版
    if yes_no(ask, "那是否需要安装原版女娲（huashu-nvwa）？[y/N] "):
        install_original(root)
        return

    # 都否 → 完成 UA 安装，标记下次再问（绝不中止）
    cfg = read_config(root)
    cfg["nvwa_deferred"] = True
    cfg.pop("nvwa_invoke", None)
    write_config(root, cfg)
    print("[nvwa] 暂不安装。universal-assistant 安装继续完成；")
    print("        下次需要蒸馏专家时，助理会再询问是否安装女娲。")


def main():
    parser = argparse.ArgumentParser(description="universal-assistant 自安装")
    parser.add_argument("--root", help="技能根目录（绝对路径）")
    parser.add_argument("--agent",
                        help="目标 agent 名（用于读环境变量推断技能根）："
                             "claude-code|codex|opencode|hermes|dsh|workbuddy|auto")
    parser.add_argument("--no-nvwa", action="store_true",
                        help="跳过女娲问答，直接进入「下次再问」状态（自动化 / 无终端）")
    args = parser.parse_args()

    src = here_dir()
    root = resolve_root(args)
    if not root:
        print("[失败] 未提供技能根目录，已取消安装。")
        sys.exit(2)

    dest = os.path.join(root, NAME)
    print("源目录 : %s" % src)
    print("目标目录: %s" % dest)

    # —— universal-assistant 永远先装好（这一步与 nvwa 无关，不因 nvwa 中止）——
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
        print("[成功] universal-assistant 已安装到 %s" % dest)

    # —— 女娲处理（任意回答都不中止）——
    if args.no_nvwa:
        cfg = read_config(root)
        cfg["nvwa_deferred"] = True
        cfg.pop("nvwa_invoke", None)
        write_config(root, cfg)
        print("[nvwa] 跳过问答（--no-nvwa），下次需要蒸馏专家时再问。")
    else:
        handle_nvwa(root, ask=input)

    print("")
    print("安装完成。请**重启你的 agent 会话**使技能生效")
    print("（DSH 有文件监听可即时生效，无需重启）。")
    print("首次激活时助理会请你给本助理起个名字。")


if __name__ == "__main__":
    main()
