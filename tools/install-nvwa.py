#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
install-nvwa.py — 安装女娲（huashu-nvwa）可选依赖（零依赖）。

固定原版地址，带**归属校验**，防止装到停更的旧镜像 xmg2024/nvwa-skill。

用法：python tools/install-nvwa.py --root <技能根> [--force]

行为：
    1. 目标 = <技能根>/huashu-nvwa
    2. 若已存在且归属正确 → 跳过
    3. 否则 git clone https://github.com/alchaincyf/nuwa-skill.git 到目标
    4. 校验：<目标>/SKILL.md frontmatter name == huashu-nvwa，且归属段指向 alchaincyf
    5. 失败（无 git / 无网）→ 给出可复制的手动命令，不静默失败

注意：clone 需要 git 与网络；若环境不具备，脚本会打印手动安装命令退出，不假装成功。
解释器：python3 / python / py -3 均可。
"""
import os
import sys
import json
import shutil
import subprocess
import argparse

NVWA_NAME = "huashu-nvwa"
NVWA_REPO = "https://github.com/alchaincyf/nuwa-skill.git"
NVWA_OFFICIAL = "github.com/alchaincyf/nuwa-skill"
STALE_MIRROR = "xmg2024/nvwa-skill"


def is_valid_nvwa(skill_dir):
    md = os.path.join(skill_dir, "SKILL.md")
    if not os.path.isfile(md):
        return False, "SKILL.md 不存在"
    try:
        with open(md, encoding="utf-8") as f:
            text = f.read()
    except Exception as e:
        return False, "读取失败: %s" % e
    name_ok = False
    official_ok = NVWA_OFFICIAL not in text  # 占位，下行再判
    in_fm = False
    for line in text.splitlines():
        if line.strip() == "---":
            in_fm = not in_fm
            continue
        if in_fm and line.startswith("name:"):
            name_ok = (line.split(":", 1)[1].strip() == NVWA_NAME)
    if not name_ok:
        return False, "frontmatter name != %s" % NVWA_NAME
    if STALE_MIRROR in text:
        return False, "检测到旧镜像 %s（停更），须替换为原版 %s" % (STALE_MIRROR, NVWA_OFFICIAL)
    if NVWA_OFFICIAL not in text:
        return False, "未找到原版归属 %s，请确认来源" % NVWA_OFFICIAL
    return True, ""


def main():
    parser = argparse.ArgumentParser(description="安装女娲 huashu-nvwa（可选依赖）")
    parser.add_argument("--root", required=True,
                        help="技能根目录（绝对路径），目标为 <root>/huashu-nvwa")
    parser.add_argument("--force", action="store_true", help="已存在时也强制重装")
    args = parser.parse_args()

    root = os.path.expanduser(args.root)
    dest = os.path.join(root, NVWA_NAME)
    print("技能根: %s" % root)
    print("目标  : %s" % dest)

    if os.path.exists(dest):
        ok, msg = is_valid_nvwa(dest)
        if ok and not args.force:
            print("[跳过] 已安装且归属正确：%s" % dest)
            print("安装完成（已存在）。请重启 agent 会话使女娲生效。")
            return
        if not ok:
            print("[警告] 已存在但校验未通过：%s" % msg)
            print("         建议删除该目录后重装：rm -rf %s" % dest)
            if not args.force:
                sys.exit(3)

    if not os.path.isdir(root):
        try:
            os.makedirs(root, exist_ok=True)
        except Exception as e:
            print("[失败] 无法创建技能根目录：%s" % e)
            sys.exit(4)

    print("克隆原版女娲：%s" % NVWA_REPO)
    try:
        r = subprocess.run(["git", "clone", NVWA_REPO, dest],
                           capture_output=True, text=True, timeout=180)
    except FileNotFoundError:
        print("[失败] 本机未安装 git。请手动执行：")
        print("  git clone %s %s" % (NVWA_REPO, dest))
        sys.exit(5)
    except Exception as e:
        print("[失败] 克隆异常：%s" % e)
        sys.exit(6)

    if r.returncode != 0:
        print("[失败] 克隆返回非零：")
        print(r.stderr)
        print("可手动执行：git clone %s %s" % (NVWA_REPO, dest))
        sys.exit(7)

    ok, msg = is_valid_nvwa(dest)
    if not ok:
        print("[失败] 安装后校验未通过：%s" % msg)
        sys.exit(8)

    print("[成功] 女娲已安装到 %s" % dest)
    print("请重启 agent 会话使女娲生效（部分 agent 有文件监听可即时生效）。")


if __name__ == "__main__":
    main()
