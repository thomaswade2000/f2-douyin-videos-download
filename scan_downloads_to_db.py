#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
扫描已有下载目录，把已下载的作品写入本地数据库（douyin_downloads.db）。

用途：媒体文件搬离本机（外置硬盘/其他设备）后，增量更新仍可
依据数据库判断已下载，避免重新下载全部文件。

用法：
    python3 scan_downloads_to_db.py                 # 默认扫描 ./Downloads/douyin
    python3 scan_downloads_to_db.py --root <目录>    # 指定扫描根目录
    python3 scan_downloads_to_db.py --dry-run        # 只预览，不写入数据库
    python3 scan_downloads_to_db.py --db <文件>      # 指定数据库文件
"""

import argparse
import re
import sqlite3
import sys
import time
from pathlib import Path

DEFAULT_DB = Path(__file__).parent / "douyin_downloads.db"
DEFAULT_ROOT = Path(__file__).parent / "Downloads" / "douyin"

SUFFIX_PATTERNS = [
    re.compile(r"^(.*)_video\.mp4$"),
    re.compile(r"^(.*)_cover\.(jpeg|webp|jpg)$"),
    re.compile(r"^(.*)_music\.mp3$"),
    re.compile(r"^(.*)_desc\.txt$"),
    re.compile(r"^(.*)_image_\d+\.(webp|jpeg|jpg|mp4)$"),
]

DIGIT_NAME = re.compile(r"^\d+\.(webp|jpeg|jpg|mp4|png)$")

SKIP_NAMES = {".DS_Store"}


def derive_key(rel_path: Path) -> str:
    """从相对路径反推作品 key（format_file_name 的输出）。"""
    name = rel_path.name
    if name in SKIP_NAMES or name.endswith(".tmp"):
        return ""

    for pattern in SUFFIX_PATTERNS:
        m = pattern.match(name)
        if m:
            return m.group(1)

    # 图集内数字命名文件：key 为父文件夹名
    if DIGIT_NAME.match(name):
        return rel_path.parent.name

    return ""


def collect_keys(root: Path) -> tuple:
    keys = set()
    skipped = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(root)
        key = derive_key(rel)
        if key:
            keys.add(key)
        else:
            skipped.append(str(rel))
    return keys, skipped


def main():
    parser = argparse.ArgumentParser(description="扫描已下载文件并写入下载记录数据库")
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT, help="扫描根目录")
    parser.add_argument("--db", type=Path, default=DEFAULT_DB, help="数据库文件路径")
    parser.add_argument("--dry-run", action="store_true", help="只预览，不写入数据库")
    args = parser.parse_args()

    if not args.root.is_dir():
        print(f"错误：目录不存在 {args.root}")
        sys.exit(1)

    keys, skipped = collect_keys(args.root)
    print(f"扫描目录: {args.root}")
    print(f"发现作品 key: {len(keys)} 个")
    if skipped:
        print(f"无法识别的文件（已跳过）: {len(skipped)} 个")
        for s in skipped[:10]:
            print(f"  - {s}")
        if len(skipped) > 10:
            print(f"  ... 等 {len(skipped)} 个")

    if args.dry_run:
        print("(dry-run) 未写入数据库")
        return

    conn = sqlite3.connect(args.db)
    try:
        conn.execute(
            """CREATE TABLE IF NOT EXISTS download_records (
                file_key TEXT PRIMARY KEY,
                aweme_id TEXT,
                created_at TEXT
            )"""
        )
        created_at = time.strftime("%Y-%m-%d %H:%M:%S")
        conn.executemany(
            "INSERT OR IGNORE INTO download_records (file_key, aweme_id, created_at) VALUES (?, '', ?)",
            [(k, created_at) for k in keys],
        )
        conn.commit()
        total = conn.execute("SELECT COUNT(*) FROM download_records").fetchone()[0]
        print(f"数据库: {args.db}")
        print(f"新增记录: {len(keys)} 条，当前总数: {total} 条")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
