FROM python:3.10-slim

WORKDIR /app

# Install system dependencies (excluding git)
# Clean up apt lists to reduce image size
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Add any other core system dependencies here if needed, but not git
    # e.g., libpq-dev for psycopg2, if you add a PostgreSQL dependency later
    # Example: libpq-dev
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# --- Pre-download models during Docker build ---
# Ensure spacy and nltk are installed via requirements.txt before these steps
RUN python -m spacy download en_core_web_sm
RUN python -m nltk.downloader wordnet

# --- Configure cache directories using Docker ENV (these take precedence) ---
ENV HF_HOME=/cache
ENV TRANSFORMERS_CACHE=/cache 
ENV NLTK_DATA=/nltk_data
ENV SPACY_DATA=/spacy_data 

# Create directories and set appropriate permissions
RUN mkdir -p /cache && chmod -R 777 /cache
RUN mkdir -p /nltk_data && chmod -R 777 /nltk_data
RUN mkdir -p /spacy_data && chmod -R 777 /spacy_data

# It's good to also create the /root/.cache for general system caching in Docker
RUN mkdir -p /root/.cache && chmod -R 777 /root/.cache 

COPY app ./app

# Expose the port your FastAPI application will run on
EXPOSE 7860

# Command to run your FastAPI application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860", "--workers", "4"]