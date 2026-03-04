# Multi-Agent SQL Optimization Framework - Production Dockerfile
FROM node:18-alpine AS frontend-builder

# Build frontend
WORKDIR /app/frontend
COPY src/package*.json ./
RUN npm ci --only=production
COPY src/ ./
RUN npm run build

# Backend
FROM python:3.9-slim AS backend

WORKDIR /app/backend
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ ./

# Copy frontend build to backend
COPY --from=frontend-builder /app/frontend/dist ./static

EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
