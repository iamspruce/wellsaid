# Use the official Python 3.10 slim image
FROM python:3.10-slim

# Set the working directory inside the container
WORKDIR /app

# Install system dependencies
# - git (optional, useful if pip dependencies are installed via git)
# - default-jre is required for language_tool_python
RUN apt-get update && apt-get install -y \
    git \
    default-jre \
 && rm -rf /var/lib/apt/lists/*

# Set environment variables
# - HF_HOME: used by Hugging Face models
# - LANGUAGE_TOOL_DOWNLOAD_DIR: used by language_tool_python
# - HOME: so that ~/.cache resolves to a writable folder
ENV HF_HOME=/cache
ENV LANGUAGE_TOOL_DOWNLOAD_DIR=/cache
ENV HOME=/app

# Create and set permissions for cache directory
RUN mkdir -p /cache && chmod -R 777 /cache

# Copy Python dependency file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Download spaCy English model
RUN python -m spacy download en_core_web_sm

# Copy application code into the container
COPY app ./app

# Expose the port (optional)
EXPOSE 7860

# Run the app using Uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860"]
