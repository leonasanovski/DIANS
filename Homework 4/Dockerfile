FROM python:3.10-slim

# Set the working directory
WORKDIR /app

# Copy only requirements first for layer caching
COPY requirements.txt /app/requirements.txt

# Install the dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application files
COPY . /app

# Expose port for Flask
EXPOSE 6000

# Run the application
CMD ["python", "app.py"]
