#!/bin/bash
# 抖音视频下载脚本 - 基于 f2
# 用法:
#   ./douyin.sh                               下载你的点赞作品（使用 config 中的主页链接）
#   ./douyin.sh likes                         下载你的点赞作品（喜欢）
#   ./douyin.sh collections                   下载你的收藏作品
#   ./douyin.sh collectsfolders               下载你的收藏夹作品（会提示选择收藏夹）
#   ./douyin.sh posts                         下载你的发布作品
#   ./douyin.sh likes <主页链接> [保存目录]    覆盖 config 中的主页链接/保存目录
# 主页链接与保存目录可写入 ./config 文件，无需每次输入。
# 增量更新：重复运行同一命令，已下载的文件会自动跳过，只下载新增视频。
#
# cookie 获取顺序：cookie.txt > 配置文件中已保存的 cookie > 自动从浏览器抓取
# 注意：从浏览器抓取 cookie 前，请登录 douyin.com 并完全关闭浏览器

set -e
cd "$(dirname "$0")"
F2="./.venv/bin/f2"
PY="./.venv/bin/python3"

# 读取本地配置（可选）：PROFILE_URL / SAVE_PATH
if [ -f ./config ]; then
  . ./config
fi

MODE="${1:-likes}"
URL="${2:-$PROFILE_URL}"
SAVE_PATH="${3:-${SAVE_PATH:-./Downloads}}"

if [ -z "$URL" ]; then
  echo "错误：未提供主页链接。请在命令行传入，或在 ./config 中设置 PROFILE_URL"
  echo "用法: ./douyin.sh <likes|collections|collectsfolders|posts> [主页链接] [保存目录]"
  exit 1
fi

case "$MODE" in
  likes)           F2_MODE="like" ;;
  collections)     F2_MODE="collection" ;;
  collectsfolders) F2_MODE="collects" ;;
  posts)           F2_MODE="post" ;;
  *) echo "未知模式: $MODE"; exit 1 ;;
esac

echo "==> 下载模式: $F2_MODE"
echo "==> 目标链接: $URL"
echo "==> 保存位置: $SAVE_PATH"

# 1) 手动保存的 cookie 优先
if [ -f ./cookie.txt ] && [ -s ./cookie.txt ]; then
  echo "==> 使用 cookie.txt 中的 cookie"
  exec $F2 dy -M "$F2_MODE" -u "$URL" -p "$SAVE_PATH" -k "$(cat ./cookie.txt)"
fi

# 2) 检查配置文件里是否已有登录 cookie（含 sessionid 才算登录态）
HAS_COOKIE=$($PY - <<'PY'
import sys
try:
    import yaml
    with open('f2/conf/app.yaml', encoding='utf-8') as f:
        d = yaml.safe_load(f)
    c = (d.get('douyin') or {}).get('cookie') or ''
    sys.stdout.write('yes' if 'sessionid' in c else 'no')
except Exception:
    sys.stdout.write('no')
PY
)

if [ "$HAS_COOKIE" = "yes" ]; then
  echo "==> 使用配置文件中已保存的登录 cookie"
  exec $F2 dy -M "$F2_MODE" -u "$URL" -p "$SAVE_PATH"
fi

# 3) 否则先从浏览器抓取 cookie（写入配置文件），再开始下载
echo "==> 配置中无登录 cookie，将从 Chrome 自动抓取"
echo "    请确保：1) 浏览器已登录 douyin.com  2) 浏览器已完全关闭（Cmd+Q）"
echo "y" | $F2 dy -M "$F2_MODE" -u "$URL" --auto-cookie chrome >/dev/null 2>&1

echo "==> cookie 已保存，开始下载"
exec $F2 dy -M "$F2_MODE" -u "$URL" -p "$SAVE_PATH"
