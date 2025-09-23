FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# System deps (if any heavy libs are needed, add here)
RUN apt-get update -y && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps
COPY backend/requirements.txt ./requirements.txt
RUN pip install --upgrade pip && pip install -r requirements.txt

# App code
COPY backend/ ./

# Models and data
COPY backend/models/fixed_rf_model.joblib ./fixed_rf_model.joblib
COPY ultimate_pickup_data.csv ./ultimate_pickup_data.csv

# Env for app
ENV RF_MODEL_PATH=./fixed_rf_model.joblib \
    PROPHET_MODEL_PATH=./prophet_model.joblib \
    CORS_ORIGINS=* \
    PORT=8080

# Expose and run
EXPOSE 8080
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "app:app", "--timeout", "600"]

