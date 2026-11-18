FROM --platform=linux/arm64 python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends build-essential libssl-dev \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY pyproject.toml ./
RUN pip install --no-cache-dir -e .
COPY . .
CMD ["python", "-m", "workers.pool"]