# Life Calendar API Server

A RESTful API server that generates responsive Life Calendar wallpapers for different device sizes (mobile, tablet, desktop).

## Features

- 🎨 **Responsive Design**: Generate wallpapers for mobile, tablet, and desktop
- 📱 **Device Presets**: Pre-configured sizes for common devices
- 🔧 **Custom Dimensions**: Specify custom width and height
- 🌐 **RESTful API**: Simple HTTP endpoints
- 🚀 **Easy Deployment**: Ready for production deployment

## Installation

### 1. Install Python Dependencies

```bash
pip3 install -r requirements_api.txt
```

### 2. Install Chromium/Chrome (for image generation)

```bash
sudo apt install chromium-browser
# or
sudo apt install chromium
```

## Usage

### Start the API Server

```bash
python3 api_server.py
```

The server will start on `http://localhost:5000`

### API Endpoints

#### 1. Get API Documentation
```bash
GET http://localhost:5000/
```

#### 2. Get Available Device Presets
```bash
GET http://localhost:5000/api/presets
```

Response:
```json
{
  "mobile": {"width": 390, "height": 844},
  "mobile-large": {"width": 428, "height": 926},
  "tablet": {"width": 768, "height": 1024},
  "desktop": {"width": 1920, "height": 1080},
  ...
}
```

#### 3. Generate Wallpaper

**Using device preset:**
```bash
GET http://localhost:5000/api/generate?device=mobile
```

**Using custom dimensions:**
```bash
GET http://localhost:5000/api/generate?width=390&height=844
```

**Get JSON response instead of image:**
```bash
GET http://localhost:5000/api/generate?device=mobile&format=json
```

#### 4. Health Check
```bash
GET http://localhost:5000/health
```

## Examples

### Generate Mobile Wallpaper

```bash
# Download image directly
curl -O "http://localhost:5000/api/generate?device=mobile"

# Or use in browser
open "http://localhost:5000/api/generate?device=mobile"
```

### Generate Custom Size

```bash
curl -O "http://localhost:5000/api/generate?width=1080&height=1920"
```

### Get JSON Response

```bash
curl "http://localhost:5000/api/generate?device=desktop&format=json"
```

## Available Device Presets

- `mobile` - 390x844 (iPhone 12/13)
- `mobile-large` - 428x926 (iPhone 14 Pro Max)
- `tablet` - 768x1024 (iPad Portrait)
- `tablet-landscape` - 1024x768 (iPad Landscape)
- `desktop` - 1920x1080 (Full HD)
- `desktop-4k` - 3840x2160 (4K UHD)

## Deployment

### Option 1: Using Gunicorn (Production)

```bash
pip3 install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 api_server:app
```

### Option 2: Using systemd Service

Create `/etc/systemd/system/lifecalendar-api.service`:

```ini
[Unit]
Description=Life Calendar API Server
After=network.target

[Service]
Type=simple
User=your-username
WorkingDirectory=/path/to/Life calender
ExecStart=/usr/bin/python3 /path/to/Life calender/api_server.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable lifecalendar-api
sudo systemctl start lifecalendar-api
```

### Option 3: Using Docker

Create `Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    chromium \
    chromium-driver \
    && rm -rf /var/lib/apt/lists/*

COPY requirements_api.txt .
RUN pip install --no-cache-dir -r requirements_api.txt

COPY . .

EXPOSE 5000

CMD ["python3", "api_server.py"]
```

Build and run:
```bash
docker build -t lifecalendar-api .
docker run -p 5000:5000 lifecalendar-api
```

### Option 4: Deploy to Cloud Platforms

#### Heroku
```bash
# Create Procfile
echo "web: gunicorn -w 4 -b 0.0.0.0:\$PORT api_server:app" > Procfile

# Deploy
heroku create your-app-name
git push heroku main
```

#### Railway
```bash
railway init
railway up
```

#### DigitalOcean App Platform
- Connect your repository
- Set build command: `pip install -r requirements_api.txt`
- Set run command: `gunicorn -w 4 -b 0.0.0.0:8080 api_server:app`

## Environment Variables

- `PORT` - Server port (default: 5000)
- `HOST` - Server host (default: 0.0.0.0)

## Troubleshooting

### Browser Not Found
If you get "No Chromium/Chrome browser found":
```bash
sudo apt install chromium-browser
```

### Permission Denied
Make sure the script is executable:
```bash
chmod +x api_server.py
```

### Port Already in Use
Change the port in `api_server.py`:
```python
app.run(host='0.0.0.0', port=8080)  # Use port 8080 instead
```

## API Response Formats

### Image Response (default)
- Content-Type: `image/png`
- Returns PNG image file
- Filename: `lifecalendar_{width}x{height}.png`

### JSON Response
- Content-Type: `application/json`
- Returns metadata about generated image
- Use `?format=json` parameter

## Mobile App Integration

### iOS (Swift)
```swift
let url = URL(string: "http://your-api.com/api/generate?device=mobile")!
URLSession.shared.downloadTask(with: url) { location, response, error in
    // Save image to Photos
}
```

### Android (Kotlin)
```kotlin
val url = "http://your-api.com/api/generate?device=mobile"
// Download and set as wallpaper
```

## License

Same as main project.
