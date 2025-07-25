# Data API service Dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY . /app

# Install Python dependencies
COPY ./app/requirements.txt .
RUN pip install --requirement requirements.txt

# Set environment variables
ENV PORT=8002
ENV HOST=0.0.0.0
ENV MONGODB_URL=mongodb://mongodb:27017
ENV MONGODB_DATABASE=investr

# Expose port
EXPOSE 8002

# Run the Data API service
CMD ["python", "-m", "investr.data.api"]
