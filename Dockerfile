# Use Playwright's official Python image which has browsers pre-installed
FROM mcr.microsoft.com/playwright/python:v1.40.0-jammy

# Set working directory
WORKDIR /app

# Install fonts for better rendering
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    fonts-liberation \
    fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

# Set Playwright browser path
ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

# Create symlinks for the Chromium binary so our API can find it
RUN CHROMIUM_PATH=$(find /ms-playwright -name "chrome" -type f -executable 2>/dev/null | head -1) && \
    if [ -n "$CHROMIUM_PATH" ]; then \
        ln -sf "$CHROMIUM_PATH" /usr/bin/chromium && \
        ln -sf "$CHROMIUM_PATH" /usr/bin/chromium-browser && \
        ln -sf "$CHROMIUM_PATH" /usr/bin/google-chrome && \
        ln -sf "$CHROMIUM_PATH" /usr/bin/chrome && \
        echo "Chromium symlinks created from: $CHROMIUM_PATH"; \
    else \
        echo "Warning: Chromium not found in expected location"; \
    fi

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
