# Use Python 3.11 slim image as base
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies including unzip
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    wget \
    unzip \
    ca-certificates \
    fonts-liberation \
    fonts-dejavu-core \
    libnss3 \
    libatk-bridge2.0-0 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    libgbm1 \
    libxss1 \
    libasound2 \
    libatspi2.0-0 \
    libgtk-3-0 \
    && rm -rf /var/lib/apt/lists/*

# Download and install Chromium from official snapshots
# Get the latest stable version number first, then download
RUN CHROMIUM_VERSION=$(wget -q -O - "https://www.googleapis.com/download/storage/v1/b/chromium-browser-snapshots/o/Linux_x64%2FLAST_CHANGE?alt=media") && \
    echo "Installing Chromium version: $CHROMIUM_VERSION" && \
    wget -q "https://commondatastorage.googleapis.com/chromium-browser-snapshots/Linux_x64/${CHROMIUM_VERSION}/chrome-linux.zip" -O /tmp/chrome.zip && \
    unzip -q /tmp/chrome.zip -d /opt/ && \
    rm /tmp/chrome.zip && \
    if [ -d /opt/chrome-linux ]; then \
        mv /opt/chrome-linux /opt/chromium; \
    else \
        echo "ERROR: Chrome extraction failed" && exit 1; \
    fi && \
    chmod +x /opt/chromium/chrome && \
    ln -sf /opt/chromium/chrome /usr/bin/chromium && \
    ln -sf /opt/chromium/chrome /usr/bin/chromium-browser && \
    ln -sf /opt/chromium/chrome /usr/bin/google-chrome && \
    ln -sf /opt/chromium/chrome /usr/bin/chrome && \
    /opt/chromium/chrome --version || echo "Chromium installed but version check failed"

# Copy requirements file
COPY requirements_api.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements_api.txt

# Copy the HTML file and API server
COPY lifecalendar.html .
COPY api_server.py .

# Create directory for temporary files
RUN mkdir -p /tmp/lifecalendar

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV FLASK_APP=api_server.py
ENV FLASK_ENV=production

# Expose port 5000
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/health')" || exit 1

# Run the Flask application
CMD ["python", "api_server.py"]
