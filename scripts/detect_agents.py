#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
detect_agents.py — 探测本机已安装的 AI agent 软件及其智能体数据位置/格式。

供「最强助理」技能在首次激活时调用：输出 JSON 到 stdout，
助理读取后按各软件格式把人设写入其智能体数据（自行拆分映射）。

扩展方式：在 REGISTRY 里加一个 detector 函数即可，返回 dict 或 None。
每个 detector 返回：
  { "software": 软件名, "path": 数据根路径, "format": 格式标记,
    "persona_file": 人设文件(或占位 <name>/<project>), "note": 写入提示 }
"""
import os
import json

HOME = os.path.expanduser("~")
APPDATA = os.environ.get("APPDATA", "")


def _found(software, path, fmt, persona_file, note):
    return {
        "software": software,
        "path": path,
        "format": fmt,
        "persona_file": persona_file,
        "note": note,
    }


def detect_workbuddy():
    p = os.path.join(HOME, ".workbuddy", "skills")
    if os.path.isdir(p):
        return _found("WorkBuddy", p, "skill_md",
                      os.path.join(p, "<name>", "SKILL.md"),
                      "把人设写成 SKILL.md，放入 skills/<名字>/ 目录")
    return None


def detect_claude_code():
    base = os.path.join(HOME, ".claude")
    md = os.path.join(base, "CLAUDE.md")
    proj = os.path.join(base, "projects")
    if os.path.isfile(md):
        return _found("Claude Code", md, "markdown", md,
                      "把人设作为指令追加进 CLAUDE.md（markdown）")
    if os.path.isdir(proj):
        return _found("Claude Code", proj, "markdown",
                      os.path.join(proj, "<project>", "CLAUDE.md"),
                      "按项目把人设写入 projects/<project>/CLAUDE.md")
    return None


def detect_cherry_studio():
    cands = [
        os.path.join(APPDATA, "Cherry Studio"),
        os.path.join(HOME, ".cherry-studio"),
        os.path.join(HOME, "AppData", "Roaming", "Cherry Studio"),
    ]
    for c in cands:
        if c and os.path.isdir(c):
            return _found("Cherry Studio", c, "json_or_db",
                          os.path.join(c, "...", "agents"),
                          "智能体多为 JSON/数据库，需按其 agents 结构写入")
    return None


def detect_openclaw_pi():
    # OpenClaw / PI 等本地 agent 框架：常见用户目录或环境变量，路径不定，留作扩展点
    cands = [
        os.path.join(HOME, ".openclaw"),
        os.path.join(HOME, ".pi"),
        os.environ.get("OPENCLAW_HOME", ""),
        os.environ.get("PI_HOME", ""),
    ]
    for c in cands:
        if c and os.path.isdir(c):
            return _found("OpenClaw/PI(推测)", c, "unknown",
                          os.path.join(c, "agents"),
                          "检测到本地 agent 框架目录，格式未知，需人工确认写入方式")
    return None


REGISTRY = [
    detect_workbuddy,
    detect_claude_code,
    detect_cherry_studio,
    detect_openclaw_pi,
]


def main():
    found = []
    for d in REGISTRY:
        try:
            r = d()
            if r:
                found.append(r)
        except Exception:
            pass
    out = {
        "detected": found,
        "count": len(found),
        "hint": "助理应逐一对 detected 项按其 format 把人设写入 persona_file；"
                "未知格式(unknown)先询问用户该软件的人设写入方式，不要猜测覆盖。",
    }
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
