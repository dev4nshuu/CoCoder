FROM python:3.11-slim

WORKDIR /app

# Install C++ compiler and necessary libraries
RUN apt-get update && \
    apt-get install -y build-essential g++ libc6-dev && \
    rm -rf /var/lib/apt/lists/*

# Copy Python requirements and install them
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all project files
COPY . .

# Expose port
EXPOSE 10000

# Run the app using gunicorn with eventlet
CMD ["sh", "-c", "gunicorn --worker-class eventlet -w 1 --bind 0.0.0.0:${PORT:-10000} app:app"]
