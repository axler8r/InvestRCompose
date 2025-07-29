# Search API service Dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY ./app/requirements.txt .
RUN pip install --requirement requirements.txt

# Copy project files
COPY . /app

# Set environment variables
ENV PORT=8003
ENV HOST=0.0.0.0

# Expose port
EXPOSE 8003

# Run the Search API service
CMD ["python", "-m", "investr.search.api"]
