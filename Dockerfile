# Use an official Python runtime as a parent image, based on a slim Debian distribution.
# 'buster' repositories are no longer actively mirrored; switching to 'bullseye'.
FROM python:3.9-slim-bullseye

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install system dependencies for Chrome (required by Selenium)
# and other necessary tools.
# 'chromium-browser' is not available on bullseye; using 'chromium'.
# Removed 'libappindicator1' and 'libindicator7' as they are often problematic or not needed for headless.
RUN apt-get update && apt-get install -y \
    wget \
    unzip \
    chromium \
    libnss3 \
    libgconf-2-4 \
    libfontconfig1 \
    libxss1 \
    fonts-liberation \
    xdg-utils \
    --no-install-recommends && \
    rm -rf /var/lib/apt/lists/*

# Install any needed Python packages specified in requirements.txt
# Ensure you have a requirements.txt file in your project root
# It should contain: Flask, pandas, pyperclip, selenium, webdriver-manager
RUN pip install --no-cache-dir -r requirements.txt

# Make port 8000 available to the world outside this container
EXPOSE 8000

# Define environment variable (updated to preferred key=value format)
ENV NAME="World"

# Run app.py when the container launches
# Replace 'app.py' with the name of your main Python application file
CMD ["python", "app1.py"]
