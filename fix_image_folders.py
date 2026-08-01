#!/usr/bin/env python3
"""重组已下载的抖音图集文件。

f2 之前会把图集的每张图片平铺保存为 `日期_标题_image_N.webp`、
实况视频为 `日期_标题_live_N.mp4`。本脚本将它们按作品分组：
  创建 `日期_标题/` 文件夹，图片重命名为 `1.webp, 2.webp, ...`，
  实况重命名为 `1.mp4, 2.mp4, ...`（与同号图片对应）。
移动后的布局与修改后的 f2 下载逻辑一致，后续增量下载仍能正确跳过。

用法:
  python3 fix_image_folders.py                 # 试运行，只列出计划
  python3 fix_image_folders.py --apply         # 实际执行
  python3 fix_image_folders.py --root <目录>   # 指定扫描根目录
"""

import argparse
import re
import sys
from pathlib import Path

IMAGE_RE = re.compile(r"^(?P<prefix>.+)_image_(?P<num>\d+)\.webp$")
LIVE_RE = re.compile(r"^(?P<prefix>.+)_live_(?P<num>\d+)\.mp4$")


def collect(root: Path) -> dict:
    """扫描目录，返回 {前缀: [(源文件, 目标文件名), ...]}"""
    groups: dict[str, list] = {}
    for p in sorted(root.rglob("*")):
        if not p.is_file() or p.name.startswith("."):
            continue
        for regex, suffix in ((IMAGE_RE, ".webp"), (LIVE_RE, ".mp4")):
            m = regex.match(p.name)
            if m:
                prefix = m.group("prefix")
                num = int(m.group("num"))
                if num <= 0:
                    break
                groups.setdefault(prefix, []).append(
                    (p, f"{num}{suffix}")
                )
                break
    return groups


def build_plan(groups: dict, apply: bool) -> list:
    plan = []
    skipped = 0
    for prefix, files in sorted(groups.items()):
        parent = files[0][0].parent
        folder = parent / prefix
        for src, new_name in files:
            dst = folder / new_name
            if src == dst:
                continue
            if dst.exists():
                print(f"  [跳过-冲突] {src.name} -> {dst} (目标已存在)")
                skipped += 1
                continue
            plan.append((src, dst, folder))
    return plan, skipped


def main() -> int:
    default_root = Path(__file__).resolve().parent / "Downloads" / "douyin"
    ap = argparse.ArgumentParser(description="重组已下载的抖音图集文件")
    ap.add_argument("--root", type=Path, default=default_root, help="扫描根目录")
    ap.add_argument(
        "--apply", action="store_true", help="实际执行移动（不加则只试运行）"
    )
    args = ap.parse_args()

    root = args.root
    if not root.is_dir():
        print(f"错误：目录不存在：{root}")
        return 1

    groups = collect(root)
    if not groups:
        print("没有找到需要重组的图集文件")
        return 0

    total_files = sum(len(files) for files in groups.values())
    print(f"扫描目录：{root}")
    print(f"发现 {len(groups)} 个图集作品，共 {total_files} 个文件")
    print()

    plan, skipped = build_plan(groups, args.apply)

    if not plan:
        print("没有需要移动的文件（可能已重组过）")
        return 0

    for src, dst, _ in plan:
        print(f"  {src.name}")
        print(f"    -> {dst.relative_to(root.parent.parent)}")

    if not args.apply:
        print()
        print(f"试运行：共 {len(plan)} 个文件将被移动，{skipped} 个因冲突跳过。")
        print("确认无误后，使用 --apply 参数实际执行。")
        return 0

    print()
    moved = 0
    for src, dst, folder in plan:
        folder.mkdir(parents=True, exist_ok=True)
        try:
            src.rename(dst)
            moved += 1
        except OSError as e:
            print(f"  [失败] {src.name}: {e}")

    print(f"完成：移动 {moved}/{len(plan)} 个文件，{skipped} 个冲突跳过")
    return 0


if __name__ == "__main__":
    sys.exit(main())
