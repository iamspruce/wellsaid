FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y git && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt


RUN python -m spacy download en_core_web_sm


ENV HF_HOME=/cache
RUN mkdir -p /cache && chmod -R 777 /cache


RUN mkdir -p /.cache && chmod -R 777 /.cache


COPY app ./app

# Expose the port your FastAPI application will run on
EXPOSE 7860

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860", "--workers", "4"]