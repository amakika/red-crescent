# Use the official Python image from Docker Hub
FROM python:3.12.8-slim

# Set environment variables
ENV PYTHONUNBUFFERED 1

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements file and install dependencies
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire project into the container
COPY . .

# Expose the port Django will run on
EXPOSE 8000

# Command to run Django application
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "redcrescent2.wsgi:application"]
