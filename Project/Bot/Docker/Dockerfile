# Stage 1: Install dependencies
FROM python:3.12-alpine AS builder

# Set the working directory
WORKDIR /app

# Install build dependencies
RUN apk add --no-cache \
    build-base \
    && rm -rf /var/cache/apk/*

# Copy the requirements file
COPY ../TelegramBot/requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Stage 2: Build the final image
FROM python:3.12-alpine

# Set the working directory
WORKDIR /app

# Set PYTHONPATH environment variable to include both /app, /app/Bot, and /app/SteamAPI
ENV PYTHONPATH=/app:/app/TgBot:/app/SteamAPI

# Copy the installed dependencies from the builder stage
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy the application code
COPY ../.. .

# Set the command to run the application
CMD ["python", "main.py"]
