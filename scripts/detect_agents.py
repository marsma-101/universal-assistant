#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
detect_agents.py — 探测本机已安装的 AI agent 软件及其智能体数据位置/格式。

供「universal-assistant」技能在首次激活时调用：输出 JSON 到 stdout，
助理读取后按各软件格式把人设写入其智能体数据。

设计原则（据审查 §3.2）：
- 只报告，不写入（写入由 agent 在用户逐项确认后执行）。默认 dry-run。
- 异常不吞：收集到 errors 数组，区分「未检测到任何受支持软件」与「探测出错」。
- 每个 detector 返回 confidence 与 write_strategy（new_file / append / manual），默认 manual。
- 未知格式标 format:"unknown" + confidence:"low"，persona_file 标为需人工确认。
- --json 输出带 schema_version 字段，字段变更时升版本。

扩展方式：在 REGISTRY 里加一个 detector 函数，返回 dict 或 None。
"""
import os
import json
import argparse

HOME = os.path.expanduser("~")
APPDATA = os.environ.get("APPDATA", "")

SCHEMA_VERSION = "1.0"

# write_strategy 取值：
#   new_file  — 新建独立文件（如 skills/<name>/SKILL.md）
#   append    — 追加到已有文件（默认不推荐，需用户明确要求）
#   manual    — 格式/路径不确定，需用户确认写入方式（默认）


def _found(software, path, fmt, persona_file, note, confidence="medium", write_strategy="manual"):
    return {
        "software": software,
        "path": path,
        "format": fmt,
        "persona_file": persona_file,
        "note": note,
        "confidence": confidence,
        "write_strategy": write_strategy,
    }


def detect_workbuddy():
    p = os.path.join(HOME, ".workbuddy", "skills")
    if os.path.isdir(p):
        return _found("WorkBuddy", p, "skill_md",
                      os.path.join(p, "<name>", "SKILL.md"),
                      "把人设写成 SKILL.md 放入 skills/<名字>/ 目录（新建独立文件）",
                      confidence="high", write_strategy="new_file")
    return None


def detect_claude_code():
    base = os.path.join(HOME, ".claude")
    md = os.path.join(base, "CLAUDE.md")
    proj = os.path.join(base, "projects")
    if os.path.isfile(md) or os.path.isdir(proj):
        # 默认建议新建独立技能文件，不追加全局 CLAUDE.md
        return _found("Claude Code", base, "skill_md_or_markdown",
                      os.path.join(base, "skills", "<name>", "SKILL.md"),
                      "优先新建 skills/<name>/SKILL.md；仅当用户明确要求时才追加全局 CLAUDE.md",
                      confidence="high", write_strategy="new_file")
    return None


def detect_cherry_studio():
    cands = [
        os.path.join(APPDATA, "Cherry Studio"),
        os.path.join(HOME, ".cherry-studio"),
        os.path.join(HOME, "AppData", "Roaming", "Cherry Studio"),
    ]
    for c in cands:
        if c and os.path.isdir(c):
            # 真实写入路径随版本变化，不猜；标 unknown + low，交由用户确认
            return _found("Cherry Studio", c, "unknown",
                          os.path.join(c, "<agents_dir>", "agents.json"),
                          "智能体多为 JSON/数据库，真实路径随版本变化，需用户确认 agents 目录与写入方式",
                          confidence="low", write_strategy="manual")
    return None


def detect_openclaw_pi():
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
                          "检测到本地 agent 框架目录，格式未知，需人工确认写入方式（confidence low）",
                          confidence="low", write_strategy="manual")
    return None


REGISTRY = [
    detect_workbuddy,
    detect_claude_code,
    detect_cherry_studio,
    detect_openclaw_pi,
]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true", help="输出 JSON（默认即是）")
    parser.add_argument("--dry-run", action="store_true", help="仅探测不写入（默认行为，保留以明示）")
    args = parser.parse_args()

    found = []
    errors = []
    for d in REGISTRY:
        try:
            r = d()
            if r:
                found.append(r)
        except Exception as e:
            errors.append({"detector": getattr(d, "__name__", str(d)), "error": str(e)})

    out = {
        "schema_version": SCHEMA_VERSION,
        "detected": found,
        "count": len(found),
        "errors": errors,
        "status": "ok" if not errors else "partial",
        "hint": "脚本只探测、不写入。助理应：逐一对 detected 项按 format+write_strategy 生成改动清单 → "
                "用户逐项确认 → 备份原文件 → 写入 → 回读校验。"
                "unknown 格式(confidence=low)先询问用户该软件的人设写入方式，不要猜测覆盖。"
                "errors 非空表示探测过程出错，应与‘未检测到’区分对待。",
    }
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
