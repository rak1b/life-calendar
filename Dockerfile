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

# Install Chromium using package manager (handles architecture automatically)
# This is the most reliable method as it ensures correct architecture
RUN set -eux; \
    apt-get update; \
    # Try installing chromium from default repos
    if apt-cache show chromium >/dev/null 2>&1; then \
        apt-get install -y --no-install-recommends chromium chromium-driver; \
    # Try chromium-browser if chromium not available
    elif apt-cache show chromium-browser >/dev/null 2>&1; then \
        apt-get install -y --no-install-recommends chromium-browser; \
    # Try backports
    else \
        echo "deb http://deb.debian.org/debian bookworm-backports main" >> /etc/apt/sources.list.d/backports.list 2>/dev/null || \
        echo "deb http://deb.debian.org/debian bullseye-backports main" >> /etc/apt/sources.list.d/backports.list; \
        apt-get update; \
        apt-get install -y --no-install-recommends -t bookworm-backports chromium 2>/dev/null || \
        apt-get install -y --no-install-recommends -t bullseye-backports chromium 2>/dev/null || \
        apt-get install -y --no-install-recommends chromium-browser; \
    fi; \
    apt-get clean; \
    rm -rf /var/lib/apt/lists/*

# Verify Chromium installation and create symlinks
RUN CHROMIUM_CMD=$(command -v chromium || command -v chromium-browser || echo "") && \
    if [ -z "$CHROMIUM_CMD" ]; then \
        echo "ERROR: Chromium not found. Attempting fallback download..."; \
        # Fallback: Download Chromium binary with architecture detection
        ARCH=$(dpkg --print-architecture || uname -m) && \
        echo "Detected architecture: $ARCH" && \
        if [ "$ARCH" = "amd64" ] || [ "$ARCH" = "x86_64" ]; then \
            CHROMIUM_ARCH="Linux_x64"; \
        elif [ "$ARCH" = "arm64" ] || [ "$ARCH" = "aarch64" ]; then \
            CHROMIUM_ARCH="Linux_ARM64"; \
        else \
            echo "ERROR: Unsupported architecture for Chromium download: $ARCH"; \
            exit 1; \
        fi && \
        CHROMIUM_VERSION=$(wget -q -O - "https://www.googleapis.com/download/storage/v1/b/chromium-browser-snapshots/o/${CHROMIUM_ARCH}%2FLAST_CHANGE?alt=media") && \
        echo "Downloading Chromium ${CHROMIUM_VERSION} for ${CHROMIUM_ARCH}" && \
        wget -q "https://commondatastorage.googleapis.com/chromium-browser-snapshots/${CHROMIUM_ARCH}/${CHROMIUM_VERSION}/chrome-linux.zip" -O /tmp/chrome.zip && \
        unzip -q /tmp/chrome.zip -d /opt/ && \
        rm /tmp/chrome.zip && \
        mv /opt/chrome-linux /opt/chromium && \
        chmod +x /opt/chromium/chrome && \
        CHROMIUM_CMD="/opt/chromium/chrome"; \
    fi && \
    echo "Using Chromium: $CHROMIUM_CMD" && \
    # Verify it works
    $CHROMIUM_CMD --version && \
    # Create symlinks
    ln -sf "$CHROMIUM_CMD" /usr/bin/chromium && \
    ln -sf "$CHROMIUM_CMD" /usr/bin/chromium-browser && \
    ln -sf "$CHROMIUM_CMD" /usr/bin/google-chrome && \
    ln -sf "$CHROMIUM_CMD" /usr/bin/chrome && \
    echo "Chromium installed successfully at: $CHROMIUM_CMD"

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
