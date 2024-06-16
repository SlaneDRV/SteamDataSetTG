# Use the official Python 3.12-alpine image as the base image for the build stage
FROM python:3.12-alpine AS builder

# Set the working directory inside the container
WORKDIR /build

# Install build dependencies (build-base includes GCC, libc-dev, and make)
RUN apk add --no-cache build-base

# Copy the requirements file into the container
COPY ./TelegramBot/requirements.txt /build/

# Install the Python dependencies specified in the requirements file
RUN pip install --no-cache-dir -r requirements.txt

# Use the official Python 3.12-alpine image as the base image for the final stage
FROM python:3.12-alpine

# Set the working directory inside the container
WORKDIR /app

# Set the PYTHONPATH environment variable to include the necessary directories
ENV PYTHONPATH=/app:/app/TelegramBot:/app/SteamAPI

# Copy the installed Python packages from the builder stage to the final stage
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages

# Copy the TelegramBot and SteamAPI directories into the container
COPY ./TelegramBot /app/TelegramBot
COPY ./SteamAPI /app/SteamAPI

# Set the default command to run the Telegram bot
CMD ["python", "/app/TelegramBot/main.py"]
