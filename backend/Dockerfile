# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Install system dependencies if any are needed (none specified for now)
# RUN apt-get update && apt-get install -y --no-install-recommends \
#     gcc \
#     && rm -rf /var/lib/apt/lists/*

# Copy the requirements file into the container at /app
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container at /app
COPY . .

# Expose the port the app runs on (Railway uses dynamic PORT)
EXPOSE 8000

# Run the application using shell form to expand $PORT environment variable
# Railway sets PORT dynamically; default to 8000 for local development
CMD uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}
