# Stage 1: Install dependencies
FROM python:3.12-alpine AS builder
WORKDIR /build

# Install build dependencies
RUN apk add --no-cache build-base

# Copy the requirements file and install Python dependencies
COPY ./TelegramBot/requirements.txt /build/
RUN pip install --no-cache-dir -r requirements.txt

# Stage 2: Build the final image
FROM python:3.12-alpine
WORKDIR /app

# Set PYTHONPATH environment variable to include the app and its subdirectories
ENV PYTHONPATH=/app:/app/TelegramBot:/app/SteamAPI

# Copy the installed dependencies from the builder stage
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages

# Copy the application code
COPY ./TelegramBot /app/TelegramBot
COPY ./SteamAPI /app/SteamAPI

# Set the command to run the application
CMD ["python", "/app/TelegramBot/main.py"]
