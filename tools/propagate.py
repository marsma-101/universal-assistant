#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
propagate.py — 跨软件写入人设（可选增强工具，默认不执行）。

⚠️ 这是「高权限、低频次」工具。**核心技能 SKILL.md 不会自动调用它**；
   只有用户明确想要「把自己的本助理人设也写进其它 AI agent 软件」时，才由 agent 显式调用。

安全约定（据改进计划 §2.4）：
    1. 先出「改动清单」给用户看（--apply 之前，默认 dry-run 只打印+记录计划）。
    2. 用户逐项确认后才写（--apply 时对每个条目交互确认；非交互环境请由调用方先收集确认）。
    3. 写入前备份原文件为 <原文件名>.bak.<时间戳>。
    4. 写入后回读校验。
    5. 写 install-manifest.json 留痕（记录每个写入项的路径/动作/备份路径），保证卸载可逆。

计划文件格式（--plan plan.json）：
[
  {"software": "Claude Code",
   "file": "/abs/path/to/skills/universal-assistant/SKILL.md",
   "action": "new_file",                 # new_file | append
   "content": "<要写入的人设文本>",
   "note": "新建独立技能文件"}
]

用法：
    python tools/propagate.py --plan plan.json            # dry-run：打印清单 + 写 planned manifest
    python tools/propagate.py --plan plan.json --apply    # 逐项确认后真正写入 + 写 install-manifest.json
    python tools/propagate.py --uninstall                 # 按 install-manifest.json 还原备份

解释器：python3 / python / py -3 均可。
"""
import os
import sys
import json
import shutil
import argparse
from datetime import datetime

MANIFEST = "install-manifest.json"


def ts():
    return datetime.now().strftime("%Y%m%d-%H%M%S")


def backup(path):
    bak = "%s.bak.%s" % (path, ts())
    shutil.copy2(path, bak)
    return bak


def write_one(item, apply_):
    software = item.get("software", "?")
    path = item.get("file", "")
    action = item.get("action", "new_file")
    content = item.get("content", "")
    note = item.get("note", "")
    print("  - [%s] %s  (%s)" % (software, path, action))
    print("      说明: %s" % note)
    if not apply_:
        return {"status": "planned", "file": path}
    if not path:
        return {"status": "error", "file": path, "error": "缺少 file"}
    try:
        if action == "append":
            if os.path.exists(path):
                bak = backup(path)
            else:
                bak = None
            with open(path, "a", encoding="utf-8") as f:
                f.write("\n" + content)
        else:  # new_file
            d = os.path.dirname(path)
            if d:
                os.makedirs(d, exist_ok=True)
            if os.path.exists(path):
                bak = backup(path)
            else:
                bak = None
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
        # 回读校验
        with open(path, encoding="utf-8") as f:
            written = f.read()
        ok = content.strip() in written or (action == "append" and content.strip() in written)
        return {"status": "written" if ok else "verify_fail", "file": path,
                "backup": bak, "note": note}
    except Exception as e:
        return {"status": "error", "file": path, "error": str(e)}


def main():
    parser = argparse.ArgumentParser(description="propagate：跨软件写入人设（可选工具）")
    parser.add_argument("--plan", help="计划 JSON 文件（改动清单）")
    parser.add_argument("--apply", action="store_true", help="真正写入（默认 dry-run 只打印+记录计划）")
    parser.add_argument("--uninstall", action="store_true", help="按 install-manifest.json 还原备份")
    args = parser.parse_args()

    if args.uninstall:
        if not os.path.isfile(MANIFEST):
            print("[失败] 找不到 %s，无法卸载。" % MANIFEST)
            sys.exit(1)
        with open(MANIFEST, encoding="utf-8") as f:
            m = json.load(f)
        for item in m.get("writes", []):
            bak = item.get("backup")
            path = item.get("file")
            if bak and os.path.isfile(bak) and path:
                shutil.copy2(bak, path)
                print("[还原] %s <- %s" % (path, bak))
        print("[完成] 已按 manifest 还原备份。")
        return

    if not args.plan:
        print("用法：--plan plan.json [--apply] | --uninstall")
        sys.exit(2)
    try:
        with open(args.plan, encoding="utf-8") as f:
            plan = json.load(f)
    except Exception as e:
        print("[失败] 读取计划文件失败：%s" % e)
        sys.exit(3)

    print("=== 改动清单（%s）===" % ("DRY-RUN" if not args.apply else "APPLY"))
    records = []
    for item in plan:
        if args.apply:
            ans = input("  确认写入上述项? [y/N]: ").strip().lower()
            if ans != "y":
                records.append({"status": "skipped", "file": item.get("file", "")})
                continue
        r = write_one(item, args.apply)
        records.append(r)

    if args.apply:
        manifest = {"generated": ts(), "writes": records}
        with open(MANIFEST, "w", encoding="utf-8") as f:
            json.dump(manifest, f, ensure_ascii=False, indent=2)
        print("[完成] 已写入 %s（留痕，便于卸载）。" % MANIFEST)
    else:
        print("[DRY-RUN] 未写入任何文件。确认无误后加 --apply 执行（会逐项交互确认）。")


if __name__ == "__main__":
    main()
