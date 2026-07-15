FROM python:3.12-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY pyproject.toml README.md ./
COPY xiaomi_camera_toolkit ./xiaomi_camera_toolkit
RUN pip install --no-cache-dir .

ENTRYPOINT ["xiaomi-camera-toolkit"]
