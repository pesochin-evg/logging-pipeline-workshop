# Используем явное указание платформы для совместимости с Kubernetes
# Для сборки используйте: docker buildx build --platform linux/amd64 -t <image> .
FROM --platform=linux/amd64 python:3.11-slim

WORKDIR /app

COPY app.py .

CMD ["python", "app.py"]
