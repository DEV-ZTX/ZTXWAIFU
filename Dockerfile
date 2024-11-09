# Use an official Python runtime as a base image
FROM python:3.9-slim-buster

# Set environment variable to prevent Python from buffering stdout and stderr
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1

# Install system dependencies
RUN apt update && apt install --no-install-recommends -y \
    bash \
    curl \
    git \
    libffi-dev \
    libjpeg62-turbo-dev \
    libwebp-dev \
    libpq-dev \
    libcurl4-openssl-dev \
    libxml2-dev \
    libxslt1-dev \
    ffmpeg \
    gcc \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip and install dependencies
RUN pip install --upgrade pip setuptools

# Set the working directory
WORKDIR /app

# Copy project files to the working directory
COPY . .

# Install required Python packages from requirements.txt
RUN pip install -r requirements.txt

# Command to start the bot (replace 'your_bot_script.py' with your main script)
CMD ["python", "your_bot_script.py"]
