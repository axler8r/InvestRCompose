# Web service Dockerfile
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
ENV FLASK_APP=investr.web.app:create_app
ENV FLASK_ENV=production
ENV PORT=5000

# Expose port
EXPOSE 5000

# Run the Flask application
CMD ["python", "-m", "investr.web.app"]
