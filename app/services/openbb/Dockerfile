# OpenBB API service Dockerfile
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
ENV PORT=8001
ENV HOST=0.0.0.0

# Expose port
EXPOSE 8001

# Run the OpenBB API service
CMD ["python", "-m", "investr.openbb.api"]
