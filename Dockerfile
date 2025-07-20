# Use Python 3.11 slim as base image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install jq first (required for parsing JSON response from Chrome for Testing API)
RUN apt-get update && apt-get install -y jq

# Install system dependencies for Chrome and Selenium
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    unzip \
    curl \
    xvfb \
    && wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

# Install ChromeDriver
# Get the installed Chrome version
RUN CHROME_VERSION=$(google-chrome --version | grep -oP \'\\d+\\.\\d+\\.\\d+\\.\\d+\') && \
    echo "Detected Chrome Version: $CHROME_VERSION" && \
    # Extract major version
    CHROME_MAJOR_VERSION=$(echo $CHROME_VERSION | cut -d\'.\' -f1) && \
    echo "Detected Chrome Major Version: $CHROME_MAJOR_VERSION" && \
    # Get the corresponding ChromeDriver version URL
    CHROMEDRIVER_VERSION_URL=$(curl -sS "https://googlechromelabs.github.io/chrome-for-testing/last-known-good-versions-with-downloads.json" | \
    jq -r ".channels.Stable.version") && \
    echo "Detected ChromeDriver Version URL: $CHROMEDRIVER_VERSION_URL" && \
    # Download ChromeDriver
    wget -q --continue -P /tmp/ "https://edgedl.me.gvt1.com/edgedl/chrome/chrome-for-testing/$CHROMEDRIVER_VERSION_URL/linux64/chromedriver-linux64.zip" && \
    unzip -qq /tmp/chromedriver-linux64.zip -d /opt/ && \
    mv /opt/chromedriver-linux64/chromedriver /usr/local/bin/chromedriver && \
    rm -rf /opt/chromedriver-linux64 /tmp/chromedriver-linux64.zip && \
    chmod +x /usr/local/bin/chromedriver

# Copy application files
COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Set environment variables for Chrome
ENV DISPLAY=:99
ENV CHROME_BIN=/usr/bin/google-chrome
ENV CHROMEDRIVER_PATH=/usr/local/bin/chromedriver

# Expose port
EXPOSE 8000

# Start command with virtual display for headless Chrome
CMD ["sh", "-c", "Xvfb :99 -screen 0 1024x768x24 > /dev/null 2>&1 & uvicorn api:app --host 0.0.0.0 --port 8000"]
