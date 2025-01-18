# Use the official Python base image
FROM python:3.10-slim

# Set the working directory
WORKDIR /app

# Copy the requirements file
COPY requirements.txt /app/requirements.txt

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the microservice code
COPY . /app

# Expose the port the microservice runs on
EXPOSE 5003

# Command to run the analysis microservice
CMD ["python", "analysis.py"]