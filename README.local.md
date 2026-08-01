# 抖音下载器（本地定制版）

个人使用的抖音（Douyin）视频下载工具，基于开源项目 [f2](https://github.com/Johnserf-Seed/f2)（v0.0.1.7）定制。

用途：下载自己抖音账号的**点赞（喜欢）作品、收藏作品、收藏夹作品**，支持**增量更新**（已下载的文件自动跳过）。

## 环境

- 位置：`~/f2`
- Python 虚拟环境：`~/f2/.venv`（Python 3.12，f2 以可编辑模式安装）
- 依赖：f2 0.0.1.7 及全部自带依赖

## 本地改动

对 f2 源码做了 3 处小补丁（`f2/apps/douyin/dl.py`），**升级 f2 或重新克隆后会失效，需重打**：

1. **图集单独建文件夹**：图集作品（`aweme_type == 68`）下载到 `<作者目录>/<日期_标题>/` 子文件夹，不再把每张图平铺在作者目录
2. **图片阿拉伯数字命名**：图集内图片命名为 `1.webp、2.webp、...`（第 N 张）
3. **实况视频同号命名**：实况照片视频命名为 `1.mp4、2.mp4、...`，与对应图片同号

普通视频不受影响，仍为 `<日期>_<标题>_video.mp4` 平铺保存。

## 快速使用

```bash
cd ~/f2

./douyin.sh             # 默认下载点赞作品（主页链接读取 config）
./douyin.sh likes       # 下载点赞（喜欢）作品
./douyin.sh collections # 下载收藏作品
./douyin.sh collectsfolders  # 下载收藏夹作品（会提示选择收藏夹）
./douyin.sh posts       # 下载发布作品

./douyin.sh likes <主页链接> [保存目录]   # 临时覆盖 config 中的链接/目录
```

### 配置文件 `~/f2/config`

```
PROFILE_URL="https://www.douyin.com/user/<你的主页链接>"
SAVE_PATH="./Downloads"
```

主页链接和保存目录写在这里后，运行 `douyin.sh` 无需再输入参数。命令行显式传参优先级更高。

### Cookie 获取顺序

1. `~/f2/cookie.txt`（手动保存的完整 cookie，优先级最高）
2. f2 配置文件 `f2/conf/app.yaml` 中已保存的登录 cookie
3. 自动从 Chrome 抓取（需先在浏览器登录 douyin.com，并完全关闭浏览器）

注意：下载**自己**的点赞/收藏作品必须使用登录态 cookie（含 `sessionid`）。

## 增量更新

已下载的文件会自动跳过。定期重复运行同一命令即可，只下载新增内容：

```bash
cd ~/f2 && ./douyin.sh
```

## 图集重组脚本 `fix_image_folders.py`

f2 补丁之前的旧下载中，图集图片是平铺保存的（`<日期_标题>_image_N.webp`）。
本脚本将旧文件重组为新结构（已执行过，日常无需再跑）：

```bash
python3 fix_image_folders.py           # 试运行，仅列出计划
python3 fix_image_folders.py --apply   # 实际执行
python3 fix_image_folders.py --root <目录>  # 指定扫描根目录
```

脚本幂等，可重复运行。

## 下载目录结构

```
~/f2/Downloads/douyin/like/<作者名>/
├── 2024-01-01 12-00-00_作品标题_video.mp4      # 普通视频（平铺）
└── 2024-01-02 12-00-00_#作品标题/              # 图集（独立文件夹）
    ├── 1.webp
    ├── 1.mp4      # 实况照片视频（与 1.webp 同号）
    ├── 2.webp
    └── ...
```

文件名的日期为**作品发布时间**（非点赞时间），来自抖音 API 的 `create_time` 字段。

## 注意事项

- 修改后的 f2 是本地可编辑安装（`pip install -e`），改动直接生效
- 如用 `pip install -U f2` 或重新克隆源码，`dl.py` 的 3 处补丁需要重打
- 下载完成后日志若出现 `api.day.app 405` 属 Bark 手机通知失败（已默认关闭），不影响下载
