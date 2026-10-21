# Frontend: Streamlit chat UI
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY frontend/ frontend/

# The cloud provider sets PORT; default to 8501 locally
ENV PORT=8501
EXPOSE 8501

CMD ["sh", "-c", "streamlit run frontend/streamlit_app.py --server.port ${PORT} --server.address 0.0.0.0 --server.headless true"]
