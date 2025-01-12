FROM python:3.9-slim

WORKDIR /app

# Combine all apt-get commands and clean up in the same layer
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libsm6 \
    libxext6 \
    git \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt ./

# Combine pip installations into a single layer
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir \
    python-telegram-bot[job-queue] \
    git+https://github.com/openai/CLIP.git \
    pytz \
    opencv-python \
    websockets==13.1 \
    ultralytics

# Download model and initialize it
RUN wget https://github.com/ultralytics/assets/releases/download/v8.3.0/yolov8s-world.pt && \
    python -c "from ultralytics import YOLOWorld; model = YOLOWorld('yolov8s-world'); model.set_classes(['person, car'])"

# Copy application files
COPY main.py bot.py ./