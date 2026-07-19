# 04_backend/Dockerfile
# Imagem de DESENVOLVIMENTO do backend FastAPI (BL-02).
# Build context: ../04_backend (ver 05_infra/docker-compose.yml e DEC-09).
FROM python:3.12-slim

# Bibliotecas de sistema exigidas pelo WeasyPrint para geração de PDF (DEC-01).
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf-2.0-0 \
    libcairo2 \
    libffi-dev \
    shared-mime-info \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
