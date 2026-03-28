FROM python:3.12-slim

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
        curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /usr/app

# Install the agent package
COPY pyproject.toml ./
COPY agent/ ./agent/
RUN pip install --no-cache-dir .

ENTRYPOINT ["tail", "-f", "/dev/null"]
