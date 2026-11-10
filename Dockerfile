# Lightweight Python production runtime
FROM python:3.10-slim

# Prevent Python from writing .pyc and buffer stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install system-level build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python requirements
COPY backend/requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir jinja2 uvicorn streamlit plotly pytest httpx

# Copy project source tree
COPY . /app

EXPOSE 8000 8501

# Default launch command runs the FastAPI production server with embedded UI
CMD ["uvicorn", "backend.api:app", "--host", "0.0.0.0", "--port", "8000"]