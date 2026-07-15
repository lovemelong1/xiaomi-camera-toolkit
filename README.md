# xiaomi-camera-toolkit

一个面向 NAS/Docker 的小米摄像头录像处理工具。它借鉴了 [hslr-s/xiaomi-camera-merge](https://github.com/hslr-s/xiaomi-camera-merge) 的“扫描小米录像片段，再用 ffmpeg 生成结果”的思路，但支持更多目录格式，并且默认优先生成体积很小的按天延时摄影。

这个项目适合这类场景：小米摄像头录像按小时、按分钟、按设备目录不断堆积在 NAS 上，占用空间很快；你希望每天自动生成一个 10 秒左右的延时摄影，确认一天内发生过什么，然后删除超过保留天数的源文件。

## 功能

- 自动识别多种小米摄像头录像目录格式
- 按天生成 10 秒左右延时摄影
- 输出自动按月份分类
- 可选把小时/分钟片段压缩合并成每日录像
- Docker 一次性运行或常驻定时运行
- 成功生成后可删除超过保留天数的源文件

## 推荐用法

大多数 NAS 用户建议只使用默认的 `timelapse` 模式：

```bash
MODE=timelapse
FRAMES=30
FPS=3
DELETE_SOURCE=true
KEEP_DAYS=15
```

也就是：每天抽 30 帧，按 3 FPS 生成大约 10 秒的延时摄影；输出成功后，只删除 15 天以前的源文件。

## 支持格式

自动识别下面几种格式，可以混在同一个输入目录里：

| 名称 | 示例 |
| --- | --- |
| 扁平区间文件 | `00_20260630000514_20260630001718.mp4` |
| GitHub 原项目小时目录 | `2026032013/00M43S_1768395643.mp4` |
| 设备 ID + 小时目录 | `607ea4aade93/2026032013/00M43S_1768395643.mp4` |

## 输出结构

默认输出到 `OUTPUT_DIR`，并按月份分类：

```text
OUTPUT_DIR/
  延时摄影/
    202607/
      20260701.mp4
  日期录像/
    202607/
      20260701.mp4
```

## 快速运行

先构建镜像：

```bash
docker build -t xiaomi-camera-toolkit .
```

处理“设备 ID + 小时目录”的录像：

```bash
docker run --rm \
  -v /volume3/16TB/xiaomi_camera_videos:/data/input \
  -v /volume3/16TB/合并小米录像:/data/output \
  -e MODE=timelapse \
  -e DELETE_SOURCE=true \
  -e KEEP_DAYS=15 \
  xiaomi-camera-toolkit
```

处理“扁平文件名”的录像时，只需要换输入挂载：

```bash
docker run --rm \
  -v /volume3/16TB/XiaomiCamera_00_B888809AA60B:/data/input \
  -v /volume3/16TB/合并小米录像:/data/output \
  -e MODE=timelapse \
  xiaomi-camera-toolkit
```

## 常驻每日运行

编辑 `docker-compose.yml` 里的两个挂载路径：

- `/data/input`：小米摄像头源录像目录
- `/data/output`：合并/延时摄影输出目录

然后启动：

```bash
docker compose up -d --build
```

`docker-compose.yml` 默认每天 03:00 运行一次，生成延时摄影，并在某天输出成功后删除 15 天以前的源文件。

查看日志：

```bash
docker logs -f xiaomi-camera-toolkit
```

停止：

```bash
docker compose down
```

## 配置项

| 变量 | 默认值 | 说明 |
| --- | --- | --- |
| `INPUT_DIR` | `/data/input` | 录像源目录 |
| `OUTPUT_DIR` | `/data/output` | 输出目录 |
| `MODE` | `timelapse` | `timelapse`、`merge-day`、`both` |
| `RUN_MODE` | `once` | `once` 跑一次，`scheduler` 常驻定时 |
| `SCHEDULE_TIME` | `03:00` | 常驻模式每天运行时间 |
| `INTERVAL_DAYS` | `1` | 常驻模式运行间隔天数 |
| `FRAMES` | `30` | 每天延时摄影抽帧数，`30/FPS=10秒` |
| `FPS` | `3` | 延时摄影帧率 |
| `WIDTH` | `1280` | 输出视频宽度 |
| `DELETE_SOURCE` | `false` | 成功输出后删除源文件 |
| `KEEP_DAYS` | 空 | 只删除超过 N 天的源文件 |
| `OVERWRITE` | `false` | 是否覆盖已有有效输出 |
| `DRY_RUN` | `false` | 只打印计划，不真正生成或删除 |

更多说明见 [docs/配置说明.md](docs/配置说明.md)。

## 延时摄影抽帧策略

一天会被完整覆盖，但白天权重更高：

- 00:00-06:00 权重 0.2
- 06:00-18:00 权重 1.0
- 18:00-24:00 权重 0.5

这样 10 秒视频仍能看到一整天，白天变化会更细。

## 日录像合并

`MODE=merge-day` 或 `MODE=both` 会把一天的视频片段压成一个 `日期录像/YYYYMM/YYYYMMDD.mp4`。

注意：这个模式需要完整转码，速度取决于 NAS/CPU/硬盘 I/O，通常会比延时摄影慢很多。如果你的录像量很大，建议优先只保留 `MODE=timelapse`。

## 安全删除逻辑

开启 `DELETE_SOURCE=true` 后，工具只会在某一天的输出成功生成后，才会删除这一天对应的源文件。

如果设置了 `KEEP_DAYS=15`，只删除距离今天超过 15 天的源文件。最近 15 天内的源文件会保留。

## 本地测试

```bash
PYTHONPATH=. python3 -m unittest discover -s tests
```

## 文档

- [NAS 部署指南](docs/NAS部署指南.md)
- [配置说明](docs/配置说明.md)
- [常见问题](docs/常见问题.md)

## 发布到 GitHub

```bash
git init
git branch -M main
git add .
git commit -m "Initial release"
git remote add origin git@github.com:YOUR_NAME/xiaomi-camera-toolkit.git
git push -u origin main
```
