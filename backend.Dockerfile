# Backend: FastAPI + MCP server (the MCP server runs inside this same container)
FROM python:3.11-slim

WORKDIR /app

# Install Python dependencies first (cached between builds)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy only the code the backend needs
COPY backend/ backend/
COPY mcp_server/ mcp_server/

# The cloud provider sets PORT; default to 8000 locally
ENV PORT=8000
EXPOSE 8000

CMD ["sh", "-c", "uvicorn backend.app:app --host 0.0.0.0 --port ${PORT}"]
