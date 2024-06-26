# Use a base image with Python and FastAPI
FROM python:3.11-slim

# Install necessary dependencies
RUN apt-get update && apt-get install -y python3-pip postgresql-client && rm -rf /var/lib/apt/lists/*

# Create the directory for the application
WORKDIR /app

# Copy the application files and .env file
COPY app.py /app
COPY requirements.txt /app

# mount the volume for the application
VOLUME /mnt/gcs

# Install the dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose port 8080 for the FastAPI app
EXPOSE 8080

# Run the FastAPI application
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8080"]
