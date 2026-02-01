#!/usr/bin/env python3
"""
Life Calendar API Server
Generates responsive calendar wallpapers for different device sizes
"""

from flask import Flask, send_file, request, jsonify, render_template_string
from flask_cors import CORS
import subprocess
import os
import tempfile
import shutil
from pathlib import Path
import json
import re
from datetime import datetime

app = Flask(__name__)
CORS(app)  # Enable CORS for API access

# Device presets
DEVICE_PRESETS = {
    'mobile': {'width': 390, 'height': 844},  # iPhone 12/13
    'mobile-large': {'width': 428, 'height': 926},  # iPhone 14 Pro Max
    'tablet': {'width': 768, 'height': 1024},  # iPad
    'tablet-landscape': {'width': 1024, 'height': 768},
    'desktop': {'width': 1920, 'height': 1080},
    'desktop-4k': {'width': 3840, 'height': 2160}
}

BASE_DIR = Path(__file__).parent
HTML_FILE = BASE_DIR / 'lifecalendar.html'


def create_custom_html(start_date, end_date, title):
    """Create a temporary HTML file with custom dates"""
    # Read the original HTML file
    with open(HTML_FILE, 'r') as f:
        html_content = f.read()
    
    # Replace the config values using regex
    # Match the config object and replace its values
    config_pattern = r"const config = \{[^}]+\};"
    new_config = f"""const config = {{
            yearStart: '{start_date}',
            yearEnd: '{end_date}',
            title: '{title}'
        }};"""
    
    html_content = re.sub(config_pattern, new_config, html_content)
    
    # Create a temporary file with the modified HTML
    with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as tmp_file:
        tmp_file.write(html_content)
        return tmp_file.name


def find_browser():
    """Find available Chromium/Chrome browser"""
    browsers = ['chromium', 'google-chrome', 'google-chrome-stable', 'chromium-browser', 'chrome']
    for browser in browsers:
        if shutil.which(browser):
            return browser
    return None


def generate_image(html_path, output_path, width, height):
    """Generate PNG image from HTML using headless Chrome"""
    browser = find_browser()
    if not browser:
        raise RuntimeError("No Chromium/Chrome browser found. Please install chromium-browser.")
    
    # Handle both Path objects and string paths
    if isinstance(html_path, str):
        html_uri = f"file://{html_path}"
    else:
        html_uri = f"file://{html_path.absolute()}"
    
    cmd = [
        browser,
        '--headless',
        '--no-sandbox',
        '--disable-gpu',
        '--disable-dev-shm-usage',
        '--disable-software-rasterizer',
        f'--window-size={width},{height}',
        '--hide-scrollbars',
        '--disable-web-security',
        '--disable-features=VizDisplayCompositor',
        f'--screenshot={output_path}',
        '--virtual-time-budget=3000',
        html_uri
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0 or not os.path.exists(output_path):
        raise RuntimeError(f"Failed to generate image: {result.stderr}")
    
    # Fix any solid color strip at bottom
    try:
        from PIL import Image
        img = Image.open(output_path)
        img_width, img_height = img.size
        
        def is_solid_row(img, y, width):
            first_pixel = img.getpixel((width//2, y))
            if first_pixel == (255, 255, 255) or first_pixel == (0, 0, 0):
                return True
            for x in range(0, width, 50):
                if img.getpixel((x, y)) != first_pixel:
                    return False
            return True
        
        strip_start = img_height
        for y in range(img_height-1, max(0, img_height-200), -1):
            if is_solid_row(img, y, img_width):
                strip_start = y
            else:
                break
        
        if strip_start < img_height:
            good_row = max(0, strip_start - 1)
            for y in range(strip_start, img_height):
                for x in range(img_width):
                    img.putpixel((x, y), img.getpixel((x, good_row)))
            img.save(output_path)
    except ImportError:
        pass  # PIL not available, skip fix
    except Exception:
        pass  # Skip if fix fails
    
    return output_path


# UI HTML template for URL generation
UI_HTML = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Life Calendar - URL Generator</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        :root {
            --bg-primary: #0a0a0f;
            --bg-secondary: #12121a;
            --bg-tertiary: #1a1a25;
            --accent: #6366f1;
            --accent-light: #818cf8;
            --accent-glow: rgba(99, 102, 241, 0.3);
            --text-primary: #f1f5f9;
            --text-secondary: #94a3b8;
            --text-muted: #64748b;
            --border: rgba(255, 255, 255, 0.08);
            --success: #10b981;
            --error: #ef4444;
        }
        
        body {
            font-family: 'Space Grotesk', -apple-system, BlinkMacSystemFont, sans-serif;
            background: var(--bg-primary);
            color: var(--text-primary);
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            align-items: center;
            padding: 24px 16px;
            background-image: 
                radial-gradient(ellipse 80% 50% at 50% 0%, rgba(99, 102, 241, 0.12) 0%, transparent 50%),
                radial-gradient(ellipse 60% 40% at 100% 100%, rgba(244, 114, 182, 0.08) 0%, transparent 50%);
        }
        
        .container {
            width: 100%;
            max-width: 520px;
        }
        
        header {
            text-align: center;
            margin-bottom: 32px;
        }
        
        h1 {
            font-size: 28px;
            font-weight: 700;
            margin-bottom: 8px;
            background: linear-gradient(135deg, var(--text-primary), var(--accent-light));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        
        .subtitle {
            color: var(--text-secondary);
            font-size: 14px;
        }
        
        .card {
            background: var(--bg-secondary);
            border: 1px solid var(--border);
            border-radius: 16px;
            padding: 24px;
            margin-bottom: 20px;
        }
        
        .card-title {
            font-size: 12px;
            font-weight: 600;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 16px;
        }
        
        .form-group {
            margin-bottom: 16px;
        }
        
        label {
            display: block;
            font-size: 13px;
            font-weight: 500;
            color: var(--text-secondary);
            margin-bottom: 6px;
        }
        
        input, select {
            width: 100%;
            padding: 12px 14px;
            font-family: inherit;
            font-size: 14px;
            background: var(--bg-tertiary);
            border: 1px solid var(--border);
            border-radius: 10px;
            color: var(--text-primary);
            transition: all 0.2s;
        }
        
        input:focus, select:focus {
            outline: none;
            border-color: var(--accent);
            box-shadow: 0 0 0 3px var(--accent-glow);
        }
        
        .row {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 12px;
        }
        
        .url-output {
            background: var(--bg-tertiary);
            border: 1px solid var(--border);
            border-radius: 10px;
            padding: 14px;
            font-family: 'JetBrains Mono', monospace;
            font-size: 12px;
            color: var(--accent-light);
            word-break: break-all;
            line-height: 1.5;
            min-height: 60px;
            margin-bottom: 14px;
        }
        
        .btn {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
            width: 100%;
            padding: 14px 20px;
            font-family: inherit;
            font-size: 14px;
            font-weight: 600;
            border: none;
            border-radius: 10px;
            cursor: pointer;
            transition: all 0.2s;
        }
        
        .btn-primary {
            background: var(--accent);
            color: white;
        }
        
        .btn-primary:hover {
            background: var(--accent-light);
            transform: translateY(-1px);
        }
        
        .btn-primary:active {
            transform: translateY(0);
        }
        
        .btn-secondary {
            background: var(--bg-tertiary);
            color: var(--text-primary);
            border: 1px solid var(--border);
        }
        
        .btn-secondary:hover {
            background: var(--bg-secondary);
            border-color: var(--accent);
        }
        
        .btn-row {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 12px;
        }
        
        .toast {
            position: fixed;
            bottom: 24px;
            left: 50%;
            transform: translateX(-50%) translateY(100px);
            background: var(--success);
            color: white;
            padding: 12px 24px;
            border-radius: 10px;
            font-size: 14px;
            font-weight: 500;
            opacity: 0;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            z-index: 100;
        }
        
        .toast.show {
            opacity: 1;
            transform: translateX(-50%) translateY(0);
        }
        
        .presets {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            margin-top: 8px;
        }
        
        .preset-btn {
            padding: 6px 12px;
            font-size: 12px;
            font-weight: 500;
            background: var(--bg-tertiary);
            border: 1px solid var(--border);
            border-radius: 6px;
            color: var(--text-secondary);
            cursor: pointer;
            transition: all 0.2s;
        }
        
        .preset-btn:hover {
            background: var(--accent);
            color: white;
            border-color: var(--accent);
        }
        
        .preset-btn.active {
            background: var(--accent);
            color: white;
            border-color: var(--accent);
        }
        
        footer {
            margin-top: 24px;
            text-align: center;
            color: var(--text-muted);
            font-size: 12px;
        }
        
        footer a {
            color: var(--accent-light);
            text-decoration: none;
        }
        
        @media (max-width: 480px) {
            .row, .btn-row {
                grid-template-columns: 1fr;
            }
            
            h1 {
                font-size: 24px;
            }
            
            .card {
                padding: 20px 16px;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>📅 Life Calendar</h1>
            <p class="subtitle">Generate custom calendar wallpapers</p>
        </header>
        
        <div class="card">
            <div class="card-title">Date Range</div>
            <div class="row">
                <div class="form-group">
                    <label for="startDate">Start Date</label>
                    <input type="date" id="startDate" value="2025-12-01">
                </div>
                <div class="form-group">
                    <label for="endDate">End Date</label>
                    <input type="date" id="endDate" value="2026-05-31">
                </div>
            </div>
            <div class="form-group">
                <label for="title">Title</label>
                <input type="text" id="title" value="180 DAYS" placeholder="e.g. 180 DAYS">
            </div>
            <div class="presets">
                <button class="preset-btn" data-days="30">30 Days</button>
                <button class="preset-btn" data-days="90">90 Days</button>
                <button class="preset-btn active" data-days="180">180 Days</button>
                <button class="preset-btn" data-days="365">1 Year</button>
            </div>
        </div>
        
        <div class="card">
            <div class="card-title">Device</div>
            <div class="form-group">
                <label for="device">Select Device</label>
                <select id="device">
                    <option value="mobile">Mobile (390×844)</option>
                    <option value="mobile-large">Mobile Large (428×926)</option>
                    <option value="tablet">Tablet (768×1024)</option>
                    <option value="tablet-landscape">Tablet Landscape (1024×768)</option>
                    <option value="desktop">Desktop (1920×1080)</option>
                    <option value="desktop-4k">Desktop 4K (3840×2160)</option>
                    <option value="custom">Custom Size</option>
                </select>
            </div>
            <div class="row" id="customSize" style="display: none;">
                <div class="form-group">
                    <label for="width">Width (px)</label>
                    <input type="number" id="width" value="390" min="100" max="8000">
                </div>
                <div class="form-group">
                    <label for="height">Height (px)</label>
                    <input type="number" id="height" value="844" min="100" max="8000">
                </div>
            </div>
        </div>
        
        <div class="card">
            <div class="card-title">Generated URL</div>
            <div class="url-output" id="urlOutput">Click "Generate URL" to create your link</div>
            <div class="btn-row">
                <button class="btn btn-primary" onclick="generateUrl()">
                    <svg width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101"/><path d="M10.172 13.828a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1"/></svg>
                    Generate URL
                </button>
                <button class="btn btn-secondary" onclick="copyUrl()">
                    <svg width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1"/></svg>
                    Copy URL
                </button>
            </div>
        </div>
        
        <button class="btn btn-primary" onclick="openUrl()" style="margin-bottom: 16px;">
            <svg width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M18 13v6a2 2 0 01-2 2H5a2 2 0 01-2-2V8a2 2 0 012-2h6"/><polyline points="15 3 21 3 21 9"/><line x1="10" y1="14" x2="21" y2="3"/></svg>
            Open & Download Image
        </button>
        
        <footer>
            <p>API Docs: <a href="/api/docs">/api/docs</a> • Made with ❤️</p>
        </footer>
    </div>
    
    <div class="toast" id="toast">Copied to clipboard!</div>
    
    <script>
        const baseUrl = window.location.origin;
        let generatedUrl = '';
        
        // Preset buttons
        document.querySelectorAll('.preset-btn').forEach(btn => {
            btn.addEventListener('click', function() {
                document.querySelectorAll('.preset-btn').forEach(b => b.classList.remove('active'));
                this.classList.add('active');
                
                const days = parseInt(this.dataset.days);
                const today = new Date();
                const endDate = new Date(today);
                endDate.setDate(endDate.getDate() + days);
                
                document.getElementById('startDate').value = formatDate(today);
                document.getElementById('endDate').value = formatDate(endDate);
                document.getElementById('title').value = days + ' DAYS';
                
                generateUrl();
            });
        });
        
        // Device selection
        document.getElementById('device').addEventListener('change', function() {
            const customSize = document.getElementById('customSize');
            customSize.style.display = this.value === 'custom' ? 'grid' : 'none';
            generateUrl();
        });
        
        // Auto-generate on input change
        document.querySelectorAll('input, select').forEach(el => {
            el.addEventListener('change', generateUrl);
        });
        
        function formatDate(date) {
            return date.toISOString().split('T')[0];
        }
        
        function generateUrl() {
            const start = document.getElementById('startDate').value;
            const end = document.getElementById('endDate').value;
            const title = encodeURIComponent(document.getElementById('title').value);
            const device = document.getElementById('device').value;
            
            let url = `${baseUrl}/api/generate?start=${start}&end=${end}&title=${title}`;
            
            if (device === 'custom') {
                const width = document.getElementById('width').value;
                const height = document.getElementById('height').value;
                url += `&width=${width}&height=${height}`;
            } else {
                url += `&device=${device}`;
            }
            
            generatedUrl = url;
            document.getElementById('urlOutput').textContent = url;
        }
        
        function copyUrl() {
            if (!generatedUrl) {
                generateUrl();
            }
            
            navigator.clipboard.writeText(generatedUrl).then(() => {
                showToast('Copied to clipboard!');
            }).catch(() => {
                // Fallback for older browsers
                const textarea = document.createElement('textarea');
                textarea.value = generatedUrl;
                document.body.appendChild(textarea);
                textarea.select();
                document.execCommand('copy');
                document.body.removeChild(textarea);
                showToast('Copied to clipboard!');
            });
        }
        
        function openUrl() {
            if (!generatedUrl) {
                generateUrl();
            }
            window.open(generatedUrl, '_blank');
        }
        
        function showToast(message) {
            const toast = document.getElementById('toast');
            toast.textContent = message;
            toast.classList.add('show');
            setTimeout(() => toast.classList.remove('show'), 2000);
        }
        
        // Generate initial URL
        generateUrl();
    </script>
</body>
</html>
'''


@app.route('/')
def index():
    """Serve the URL generator UI"""
    return UI_HTML


@app.route('/api/docs')
def api_docs():
    """API documentation"""
    return jsonify({
        'name': 'Life Calendar API',
        'version': '2.0.0',
        'endpoints': {
            '/api/generate': {
                'method': 'GET',
                'description': 'Generate calendar wallpaper image',
                'parameters': {
                    'device': f"Device type: {', '.join(DEVICE_PRESETS.keys())}",
                    'width': 'Custom width in pixels (optional)',
                    'height': 'Custom height in pixels (optional)',
                    'start': 'Start date in YYYY-MM-DD format (default: 2025-12-01)',
                    'end': 'End date in YYYY-MM-DD format (default: 2026-05-31)',
                    'title': 'Calendar title (default: 180 DAYS)',
                    'format': 'Response format: image (default) or json'
                },
                'examples': [
                    '/api/generate?device=mobile',
                    '/api/generate?device=mobile&start=2024-01-01&end=2024-12-31&title=2024',
                    '/api/generate?width=390&height=844&start=2024-06-01&end=2024-08-31&title=SUMMER',
                    '/api/generate?device=desktop&format=json'
                ]
            },
            '/api/presets': {
                'method': 'GET',
                'description': 'Get available device presets'
            },
            '/health': {
                'method': 'GET',
                'description': 'Health check endpoint'
            }
        }
    })


@app.route('/api/presets', methods=['GET'])
def get_presets():
    """Get available device presets"""
    return jsonify(DEVICE_PRESETS)


@app.route('/api/generate', methods=['GET'])
def generate_wallpaper():
    """Generate calendar wallpaper for specified device or dimensions"""
    custom_html_path = None
    try:
        # Get dimension parameters
        device = request.args.get('device', 'desktop')
        width = request.args.get('width', type=int)
        height = request.args.get('height', type=int)
        format_type = request.args.get('format', 'image')
        
        # Get custom date parameters
        start_date = request.args.get('start', '2025-12-01')  # Default start date
        end_date = request.args.get('end', '2026-05-31')      # Default end date
        title = request.args.get('title', '180 DAYS')          # Default title
        
        # Validate date format (YYYY-MM-DD)
        date_pattern = r'^\d{4}-\d{2}-\d{2}$'
        if not re.match(date_pattern, start_date):
            return jsonify({'error': f'Invalid start date format: {start_date}. Use YYYY-MM-DD'}), 400
        if not re.match(date_pattern, end_date):
            return jsonify({'error': f'Invalid end date format: {end_date}. Use YYYY-MM-DD'}), 400
        
        # Validate dates are valid
        try:
            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            end_dt = datetime.strptime(end_date, '%Y-%m-%d')
            if end_dt <= start_dt:
                return jsonify({'error': 'End date must be after start date'}), 400
        except ValueError as e:
            return jsonify({'error': f'Invalid date: {str(e)}'}), 400
        
        # Determine dimensions
        if width and height:
            dimensions = {'width': width, 'height': height}
        elif device in DEVICE_PRESETS:
            dimensions = DEVICE_PRESETS[device]
        else:
            return jsonify({'error': f'Unknown device: {device}. Use /api/presets to see available devices.'}), 400
        
        # Validate dimensions
        if dimensions['width'] < 100 or dimensions['height'] < 100:
            return jsonify({'error': 'Dimensions must be at least 100x100 pixels'}), 400
        if dimensions['width'] > 8000 or dimensions['height'] > 8000:
            return jsonify({'error': 'Dimensions cannot exceed 8000x8000 pixels'}), 400
        
        # Create custom HTML with the specified dates
        custom_html_path = create_custom_html(start_date, end_date, title)
        
        # Create temporary output file
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:
            output_path = tmp_file.name
        
        # Generate image using the custom HTML
        generate_image(custom_html_path, output_path, dimensions['width'], dimensions['height'])
        
        if format_type == 'json':
            # Return JSON with file info
            file_size = os.path.getsize(output_path)
            return jsonify({
                'success': True,
                'device': device,
                'dimensions': dimensions,
                'start_date': start_date,
                'end_date': end_date,
                'title': title,
                'file_size': file_size,
                'file_path': output_path,
                'message': 'Image generated successfully.'
            })
        else:
            # Return image file
            return send_file(
                output_path,
                mimetype='image/png',
                as_attachment=True,
                download_name=f'lifecalendar_{dimensions["width"]}x{dimensions["height"]}.png'
            )
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        # Clean up the custom HTML file
        if custom_html_path and os.path.exists(custom_html_path):
            try:
                os.unlink(custom_html_path)
            except:
                pass


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    browser = find_browser()
    return jsonify({
        'status': 'healthy',
        'browser_available': browser is not None,
        'browser': browser,
        'html_file_exists': HTML_FILE.exists()
    })


if __name__ == '__main__':
    # Check if HTML file exists
    if not HTML_FILE.exists():
        print(f"Error: {HTML_FILE} not found!")
        exit(1)
    
    # Check if browser is available
    browser = find_browser()
    if not browser:
        print("Warning: No Chromium/Chrome browser found. Install chromium-browser for image generation.")
    
    print("Starting Life Calendar API Server...")
    print(f"HTML file: {HTML_FILE}")
    print(f"Browser: {browser or 'NOT FOUND'}")
    print("\nAPI Endpoints:")
    print("  GET / - API documentation")
    print("  GET /api/presets - Get device presets")
    print("  GET /api/generate?device=mobile - Generate wallpaper")
    print("  GET /health - Health check")
    print("\nStarting server on http://0.0.0.0:5000")
    
    # Use production WSGI server in Docker, development server otherwise
    import os
    if os.getenv('FLASK_ENV') == 'production':
        from waitress import serve
        serve(app, host='0.0.0.0', port=5000)
    else:
        app.run(host='0.0.0.0', port=5000, debug=True)
