FROM python:3.10-slim

# Set working directory inside the container
WORKDIR /app

# Install system dependencies
# git is included for any potential future needs or if any dependency requires it for cloning
# Install Java Runtime Environment (JRE) - crucial for language-tool-python
RUN apt-get update && apt-get install -y git default-jre && rm -rf /var/lib/apt/lists/*

# Install Python dependencies from requirements.txt
# Ensure requirements.txt is copied before installing to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Download the spaCy English language model
# This is crucial for resolving the "[E050] Can't find model 'en_core_web_sm'" error
RUN python -m spacy download en_core_web_sm

# Setup Hugging Face cache directory and permissions
# This directory will also be used by language-tool-python for its main downloads.
ENV HF_HOME=/cache
RUN mkdir -p /cache && chmod -R 777 /cache

# ... other Dockerfile content ...
ENV GRAMMAFREE_API_KEY="admin" 

# Explicitly create and set permissions for /.cache
# This is to address PermissionError: [Errno 13] Permission denied: '/.cache'
# which language-tool-python might be trying to write to.
RUN mkdir -p /.cache && chmod -R 777 /.cache

# Set environment variable for language-tool-python download directory
# This redirects LanguageTool's primary downloads to the shared /cache directory.
ENV LANGUAGE_TOOL_DOWNLOAD_DIR=/cache

# Copy the entire application code into the container
# This copies your 'app' directory, including main.py, routers, models, etc.
COPY app ./app

# Command to run the FastAPI application using Uvicorn
# Binds the app to all network interfaces (0.0.0.0) on port 7860
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860"]
