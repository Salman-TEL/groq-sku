# Use the official Python image from the Docker Hub
FROM python:3.12-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file first to leverage Docker cache
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY app/ ./app/
COPY .env.example ./.env

# Copy the service account file into the container (modify this to match your file path)
COPY dev-zephyr-438008-g6-e6ff9df35d37.json /app/dev-zephyr-438008-g6-e6ff9df35d37.json

# Expose the port the app runs on
EXPOSE 8000

# Set environment variables for Flask
ENV FLASK_APP=app/app.py
ENV FLASK_ENV=development

# Command to run the application
CMD ["flask", "run", "--host=0.0.0.0", "--port=8000"]
