# One image: builds the UI, then serves UI + API from the backend on port 8000.
FROM node:20-alpine AS ui
WORKDIR /ui
COPY frontend/package*.json ./
RUN npm install --no-audit --no-fund
COPY frontend/ ./
RUN npm run build

FROM python:3.11-slim
ENV PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1 HF_HOME=/models
WORKDIR /app/backend
# CPU-only torch & torchvision keeps the image ~1.5 GB smaller and matches CPU C++ operators
RUN pip install --no-cache-dir torch torchvision --index-url https://download.pytorch.org/whl/cpu
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/app ./app
COPY backend/skills ./skills
COPY backend/seed_data ./seed_data
COPY backend/scripts ./scripts
COPY backend/seed_data.py ./seed_data.py
COPY --from=ui /ui/dist /app/frontend/dist
# Download the embedding model at build time so the first start is fast
ARG EMBEDDING_MODEL=intfloat/multilingual-e5-small
RUN python -c "from sentence_transformers import SentenceTransformer as S; S('${EMBEDDING_MODEL}')"
# Ensure /models directory is prepared for OCR and embeddings
ENV OCR_MODEL_DIR=/models/easyocr
RUN mkdir -p /models/easyocr && useradd -m -u 1000 app && chown -R app /app /models
USER app
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=90s CMD python -c "import os, urllib.request; p = os.environ.get('PORT', '8000'); urllib.request.urlopen(f'http://127.0.0.1:{p}/health')"
# 2 workers share the work safely (one of them runs sync in the background). Each loads the model (~0.5 GB RAM).
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers ${WORKERS:-2} --proxy-headers --forwarded-allow-ips='*'"]
