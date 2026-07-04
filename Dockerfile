# Use official Python runtime as base image
FROM python:3.10-slim

# Set system environment variables to optimize Python execution in containers
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=8501

# Install system dependencies required for compilation and specific libraries
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set standard working directory
WORKDIR /app

# Copy requirements file first to utilize Docker build cache layer caching
COPY requirements.txt .

# Install Python package dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy all application source code files into the container
COPY . .

# Pre-create data storage paths to avoid permission issues at runtime
RUN mkdir -p data/uploads data/papers data/chroma_db

# Expose Streamlit default communication port
EXPOSE 8501

# Healthcheck to monitor Streamlit container status
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health || exit 1

# Start the Streamlit application using production-recommended flags
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
