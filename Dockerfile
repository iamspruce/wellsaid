FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
# git might not be strictly necessary for deployment unless you're cloning repos at runtime
# but it's often useful for debugging or specific workflows.
RUN apt-get update && apt-get install -y git && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# --- Install spaCy model ---
# This downloads the small English model
RUN python -m spacy download en_core_web_sm

# --- Install NLTK WordNet data ---
# This downloads the WordNet corpus for NLTK
RUN python -m nltk.downloader wordnet

# --- Configure cache directories for Hugging Face models ---
# HF_HOME is where SentenceTransformers and other Hugging Face models will cache.
# /.cache is also a common location many libraries default to if HF_HOME isn't set,
# or for other internal caching. Setting permissions ensures the app can write there.
ENV HF_HOME=/cache
ENV TRANSFORMERS_CACHE=/cache
ENV NLTK_DATA=/nltk_data

# Create directories and set appropriate permissions
RUN mkdir -p /cache && chmod -R 777 /cache
RUN mkdir -p /root/.cache && chmod -R 777 /root/.cache 

# Ensure NLTK uses the specified data path.
# This makes subsequent 'nltk.downloader' calls store data here,
# and NLTK will look here first.
RUN python -c "import nltk; nltk.data.path.append('/nltk_data')"


COPY app ./app

# Expose the port your FastAPI application will run on
EXPOSE 7860

# Command to run your FastAPI application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860", "--workers", "4"]