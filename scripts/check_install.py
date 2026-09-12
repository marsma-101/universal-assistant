#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
check_install.py — universal-assistant 自检脚本（核心，零依赖）。

职责只有一件：**认识自己**——「我在哪个技能根、目录名是否等于 name、frontmatter 是否合法、可选依赖女娲在不在」。

设计（据改进计划 §4）：
- 每个 agent 读自己的 SKILL.md 时，天然知道自己在文件系统的位置（脚本就在技能目录内），
  因此用 __file__ 反推父目录即可，不需要扫描全机、不需要覆盖各家路径表。
- 异常不吞：收集到 errors 数组，区分「装得不对」与「探测出错」。
- 输出 JSON（带 schema_version）；--json 为兼容参数（默认即 JSON）。

用法：python scripts/check_install.py [--json]
解释器：python3 / python / py -3 均可。
"""
import os
import re
import json
import argparse

NAME = "universal-assistant"
NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
SCHEMA_VERSION = "1.0"
DESC_MAX = 1024


def read_frontmatter(skill_md):
    """返回 (frontmatter_dict, error_or_None)。"""
    try:
        with open(skill_md, encoding="utf-8") as f:
            text = f.read()
    except Exception as e:
        return None, "读取 SKILL.md 失败: %s" % e
    if not text.startswith("---"):
        return None, "缺少 frontmatter（文件未以 --- 开头）"
    parts = text.split("---", 2)
    if len(parts) < 3:
        return None, "frontmatter 未正确闭合"
    fm = {}
    for line in parts[1].splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if ":" in line:
            k, v = line.split(":", 1)
            fm[k.strip()] = v.strip()
    return fm, None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true", help="输出 JSON（默认即是）")
    args = parser.parse_args()

    errors = []
    self_info = {"dir": None, "name": None, "name_matches_dir": False,
                 "name_valid": False, "description_len": 0, "ok": False}
    dependency = {"huashu-nvwa": "missing"}
    notes = []

    try:
        here = os.path.dirname(os.path.abspath(__file__))
        skill_dir = os.path.dirname(here)  # scripts/ 的父目录 = 技能目录
        self_info["dir"] = skill_dir
        dir_name = os.path.basename(skill_dir)
        self_info["name"] = dir_name
        self_info["name_matches_dir"] = (dir_name == NAME)
        self_info["name_valid"] = bool(NAME_RE.match(dir_name)) and len(dir_name) <= 64

        if not self_info["name_matches_dir"]:
            notes.append("目录名(%s) != name(%s)；遵循 Agent Skills 规范的 agent 会静默跳过本技能，请改名或重装"
                         % (dir_name, NAME))
        if not self_info["name_valid"]:
            notes.append("目录名不符合 ^[a-z0-9]+(-[a-z0-9]+)*$ 且 ≤64 字符的规范")

        fm, err = read_frontmatter(os.path.join(skill_dir, "SKILL.md"))
        if err:
            errors.append({"check": "frontmatter", "error": err})
        else:
            fm_name = fm.get("name", "")
            desc = fm.get("description", "")
            if fm_name != NAME:
                errors.append({"check": "frontmatter.name",
                               "error": "name 字段(%s) != %s" % (fm_name, NAME)})
            self_info["description_len"] = len(desc)
            if not desc:
                errors.append({"check": "frontmatter.description", "error": "description 为空"})
            elif len(desc) > DESC_MAX:
                errors.append({"check": "frontmatter.description",
                               "error": "description 超过 %d 字符" % DESC_MAX})

        # 可选依赖：同级技能根下是否存在 huashu-nvwa/
        skill_root = os.path.dirname(skill_dir)
        nvwa_dir = os.path.join(skill_root, "huashu-nvwa")
        dependency["huashu-nvwa"] = "present" if os.path.isdir(nvwa_dir) else "missing"

        self_info["ok"] = (self_info["name_matches_dir"]
                           and self_info["name_valid"]
                           and not errors)
    except Exception as e:
        errors.append({"check": "global", "error": str(e)})

    if dependency["huashu-nvwa"] == "missing":
        notes.append("女娲(huashu-nvwa)未安装——专业领域蒸馏不可用，将降级为通用简报；"
                     "可选装：python tools/install-nvwa.py --root <技能根>")

    out = {
        "schema_version": SCHEMA_VERSION,
        "self": self_info,
        "dependency": dependency,
        "errors": errors,
        "notes": notes,
        "status": "ok" if (self_info["ok"] and not errors) else "fail",
    }
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
