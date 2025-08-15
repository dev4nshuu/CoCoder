# Official Python image as the base image
FROM python:3.11-slim

# Install necessary packages for building and running C++ programs
RUN apt-get update && apt-get install -y \
    g++ \
    build-essential \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory in the container
WORKDIR /cocoder

# Copy all project files into the container
COPY . .

# Installing Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Environment variable for the port
ENV PORT=5000

# Expose port 5000
EXPOSE 5000

# Default command to run the application
CMD ["python", "app.py"]
