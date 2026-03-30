# Stage 1: Build React frontend
# vite outDir is ../static, so from WORKDIR /frontend that's /static
FROM node:20-slim AS frontend

WORKDIR /frontend

COPY frontend/package*.json ./
RUN npm ci

COPY frontend/ .
RUN npm run build

# Stage 2: Python runtime
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source
COPY server.py db.py schema.sql ./

# Copy built frontend (vite outputs to /static = one level up from /frontend)
COPY --from=frontend /static ./static

# Create data directory for SQLite
RUN mkdir -p /app/data

CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8765"]
