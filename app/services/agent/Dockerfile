# Agent service Dockerfile
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
ENV PORT=8000
ENV MODEL_NAME=gpt-4o-mini

# Expose port
EXPOSE 8000

# Run the agent API service
CMD ["python", "-m", "investr.agent.api"]
