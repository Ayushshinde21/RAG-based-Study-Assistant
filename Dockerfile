FROM python:3.12-slim

# YOUTUBE_ENABLED=0 disables full YouTube audio downloads; caption-only processing is still attempted.
ENV APP_ENV=production \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    HF_HOME=/models \
    TOKENIZERS_PARALLELISM=false \
    WARMUP=1 \
    MAX_UPLOAD_MB=30 \
    YOUTUBE_ENABLED=0 \
    SESSION_COOKIE_SECURE=1

# ffmpeg decodes audio; nodejs is used by yt-dlp for YouTube
RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg nodejs \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# CPU-only torch (the default build pulls GBs of GPU libraries you can't use here)
RUN pip install torch --index-url https://download.pytorch.org/whl/cpu

COPY requirements-cloud.txt .
RUN pip install -r requirements-cloud.txt

# Bake the models into the image so a cold start doesn't download them
RUN python -c "from sentence_transformers import SentenceTransformer, CrossEncoder; \
SentenceTransformer('all-MiniLM-L6-v2'); \
CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')" \
 && python -c "from faster_whisper import WhisperModel; \
WhisperModel('small', device='cpu', compute_type='int8')"

# From here on, never contact Hugging Face at runtime. The models are already baked in
# above; a live check was rate-limited (HTTP 429) and made startup exceed Cloud Run's 4-minute limit.
ENV HF_HUB_OFFLINE=1 \
    TRANSFORMERS_OFFLINE=1 \
    HF_HUB_DISABLE_TELEMETRY=1

COPY . .

# Cloud Run provides $PORT (8080)
CMD exec uvicorn api:app --host 0.0.0.0 --port ${PORT:-8080}