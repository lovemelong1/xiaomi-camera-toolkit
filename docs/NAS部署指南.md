# NAS 部署指南

这份文档以群晖/普通 Docker NAS 为例，说明如何部署 `xiaomi-camera-toolkit`。

## 目录规划

推荐准备两个目录：

```text
/volume3/16TB/xiaomi_camera_videos       # 小米摄像头源录像
/volume3/16TB/合并小米录像                # 输出目录
```

输出目录会自动生成：

```text
/volume3/16TB/合并小米录像/
  延时摄影/
    202607/
      20260701.mp4
  日期录像/
    202607/
      20260701.mp4
```

## docker compose 部署

进入项目目录：

```bash
cd xiaomi-camera-toolkit
```

按你的 NAS 路径修改 `docker-compose.yml`：

```yaml
volumes:
  - /volume3/16TB/xiaomi_camera_videos:/data/input
  - /volume3/16TB/合并小米录像:/data/output
```

启动：

```bash
docker compose up -d --build
```

查看日志：

```bash
docker logs -f xiaomi-camera-toolkit
```

停止：

```bash
docker compose down
```

## 一次性运行

如果只想手动跑一次：

```bash
docker run --rm \
  -v /volume3/16TB/xiaomi_camera_videos:/data/input \
  -v /volume3/16TB/合并小米录像:/data/output \
  -e MODE=timelapse \
  -e DELETE_SOURCE=false \
  xiaomi-camera-toolkit
```

确认输出没有问题后，再打开删除：

```bash
docker run --rm \
  -v /volume3/16TB/xiaomi_camera_videos:/data/input \
  -v /volume3/16TB/合并小米录像:/data/output \
  -e MODE=timelapse \
  -e DELETE_SOURCE=true \
  -e KEEP_DAYS=15 \
  xiaomi-camera-toolkit
```

## 推荐常驻配置

```yaml
environment:
  INPUT_DIR: /data/input
  OUTPUT_DIR: /data/output
  MODE: timelapse
  RUN_MODE: scheduler
  SCHEDULE_TIME: "03:00"
  INTERVAL_DAYS: "1"
  FRAMES: "30"
  FPS: "3"
  WIDTH: "1280"
  DELETE_SOURCE: "true"
  KEEP_DAYS: "15"
```

含义：

- 每天 03:00 执行一次
- 每天生成一个约 10 秒的延时摄影
- 输出成功后删除 15 天以前的源文件
- 最近 15 天源文件继续保留
