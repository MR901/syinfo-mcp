FROM python:3.10-slim

ARG APP_DIR=/app
WORKDIR ${APP_DIR}

# System deps (optional but useful)
RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates && rm -rf /var/lib/apt/lists/*

# Copy code
COPY requirements.txt ${APP_DIR}/requirements.txt
COPY python/ ${APP_DIR}/python/
COPY VERSION README.rst .

# Install Python deps
RUN pip install --no-cache-dir --upgrade pip \
 && pip install --no-cache-dir -r requirements.txt

# Runtime env
ENV PYTHONUNBUFFERED=1 \
    PYTHONPATH=${APP_DIR}/python \
    FOGLAMP_HOST=host.docker.internal \
    FOGLAMP_PORT=8081

EXPOSE 8000

# Run the MCP server (HTTP mode as per your __main__ block)
CMD ["python", "python/foglamp/services/mcp/src/mcp_server.py"]
