# Use the official Python image from Docker Hub
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Install system dependencies including dbus
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    build-essential \
    bluez \
    libbluetooth-dev \
    dbus \
    && rm -rf /var/lib/apt/lists/*

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed Python dependencies
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

# Expose port 5000 for the Flask server
EXPOSE 5000

# Define environment variable
ENV NAME=World

# Run the application
CMD ["python", "app.py"]
