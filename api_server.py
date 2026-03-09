#!/usr/bin/env python3
"""
Life Calendar API Server
Generates responsive calendar wallpapers for different device sizes
"""

from flask import Flask, send_file, request, jsonify, send_from_directory
from flask_cors import CORS
import subprocess
import os
import tempfile
import shutil
from pathlib import Path
import json
import re
import time
import secrets
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

# Resolve to absolute path so index.html is found regardless of CWD when server runs
BASE_DIR = Path(__file__).resolve().parent
HTML_FILE = BASE_DIR / 'lifecalendar.html'
INDEX_HTML = BASE_DIR / 'index.html'  # URL generator UI (served at /)
THEME_SEED_HISTORY_FILE = BASE_DIR / '.theme_seed_history.json'
THEME_SEED_HISTORY_LIMIT = 20000


def _load_theme_seed_history():
    if not THEME_SEED_HISTORY_FILE.exists():
        return []
    try:
        with open(THEME_SEED_HISTORY_FILE, 'r') as f:
            data = json.load(f)
        if isinstance(data, list):
            return data[-THEME_SEED_HISTORY_LIMIT:]
    except (OSError, ValueError):
        pass
    return []


def _save_theme_seed_history(history):
    try:
        with open(THEME_SEED_HISTORY_FILE, 'w') as f:
            json.dump(history[-THEME_SEED_HISTORY_LIMIT:], f)
    except OSError:
        pass


def generate_unique_theme_seed():
    """Generate a unique theme seed and avoid exact repeats across runs."""
    history = _load_theme_seed_history()
    used = set(history)

    for _ in range(200):
        seed = f"{time.time_ns()}-{secrets.token_hex(12)}"
        if seed not in used:
            history.append(seed)
            _save_theme_seed_history(history)
            return seed

    # Fallback (practically unreachable)
    return f"{time.time_ns()}-{secrets.token_hex(16)}"


def create_custom_html(start_date, end_date, title):
    """Create a temporary HTML file with custom dates"""
    # Read the original HTML file
    with open(HTML_FILE, 'r') as f:
        html_content = f.read()
    
    # Replace the config values using regex
    # Match the config object and replace its values
    config_pattern = r"const config = \{[^}]+\};"
    theme_seed = generate_unique_theme_seed()
    new_config = (
        "const config = {\n"
        f"            yearStart: {json.dumps(start_date)},\n"
        f"            yearEnd: {json.dumps(end_date)},\n"
        f"            title: {json.dumps(title)},\n"
        f"            themeSeed: {json.dumps(theme_seed)}\n"
        "        };"
    )
    
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


# Scale factor for screenshot: render at higher resolution then downscale for sharper text.
SCREENSHOT_SCALE = 4


def generate_image(html_path, output_path, width, height):
    """Generate PNG image from HTML using headless Chrome.
    When Pillow is available, renders at 2x resolution then downscales for crisp text.
    """
    browser = find_browser()
    if not browser:
        raise RuntimeError("No Chromium/Chrome browser found. Please install chromium-browser.")

    # Handle both Path objects and string paths
    if isinstance(html_path, str):
        html_uri = f"file://{html_path}"
    else:
        html_uri = f"file://{html_path.absolute()}"

    # Use 2x capture only if we can downscale (Pillow required); otherwise capture at 1x
    try:
        from PIL import Image
        _pil_available = True
    except ImportError:
        _pil_available = False
    use_scale = SCREENSHOT_SCALE > 1 and _pil_available
    capture_path = output_path
    if use_scale:
        fd, capture_path = tempfile.mkstemp(suffix='.png')
        os.close(fd)

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
        f'--screenshot={capture_path}',
        '--virtual-time-budget=3000',
        html_uri
    ]
    if use_scale:
        cmd.insert(-1, f'--force-device-scale-factor={SCREENSHOT_SCALE}')

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0 or not os.path.exists(capture_path):
        if capture_path != output_path and os.path.exists(capture_path):
            try:
                os.unlink(capture_path)
            except OSError:
                pass
        raise RuntimeError(f"Failed to generate image: {result.stderr}")

    try:
        from PIL import Image, ImageFilter
        img = Image.open(capture_path).convert('RGBA')
        img_width, img_height = img.size

        # If we captured at high scale, downscale to target size with high-quality resampling.
        if SCREENSHOT_SCALE > 1 and (img_width, img_height) == (width * SCREENSHOT_SCALE, height * SCREENSHOT_SCALE):
            resample = getattr(Image, 'Resampling', Image)
            lanczos = getattr(resample, 'LANCZOS', Image.LANCZOS)
            img = img.resize((width, height), lanczos)
            # Small unsharp mask significantly improves tiny text clarity.
            img = img.filter(ImageFilter.UnsharpMask(radius=0.8, percent=120, threshold=2))

        # Fix any solid color strip at bottom
        img_width, img_height = img.size

        def is_artifact_row(pil_img, y, w):
            # Detect bottom artifact rows that are either:
            # 1) perfectly/near-solid rows, or
            # 2) very dark low-variance rows (common headless capture bar).
            samples = []
            step = max(1, w // 40)
            for x in range(0, w, step):
                r, g, b, _a = pil_img.getpixel((x, y))
                samples.append((r, g, b))

            if not samples:
                return False

            rs = [p[0] for p in samples]
            gs = [p[1] for p in samples]
            bs = [p[2] for p in samples]

            r_range = max(rs) - min(rs)
            g_range = max(gs) - min(gs)
            b_range = max(bs) - min(bs)
            avg_luma = sum((0.2126 * r + 0.7152 * g + 0.0722 * b) for r, g, b in samples) / len(samples)

            near_solid = (r_range <= 3 and g_range <= 3 and b_range <= 3)
            near_black = avg_luma <= 12 and (r_range <= 10 and g_range <= 10 and b_range <= 10)
            near_white = avg_luma >= 245 and near_solid
            return near_solid or near_black or near_white

        strip_start = img_height
        scan_depth = max(200, img_height // 3)
        for y in range(img_height - 1, max(0, img_height - scan_depth), -1):
            if is_artifact_row(img, y, img_width):
                strip_start = y
            else:
                break

        if strip_start < img_height:
            good_row = max(0, strip_start - 1)
            for y in range(strip_start, img_height):
                for x in range(img_width):
                    img.putpixel((x, y), img.getpixel((x, good_row)))

        img.save(output_path, 'PNG', optimize=True, compress_level=2)
    except ImportError:
        # PIL not available: copy capture as-is (no downscale or strip fix)
        if capture_path != output_path:
            shutil.copy2(capture_path, output_path)
    except Exception:
        if capture_path != output_path:
            shutil.copy2(capture_path, output_path)
    finally:
        if capture_path != output_path and os.path.exists(capture_path):
            try:
                os.unlink(capture_path)
            except OSError:
                pass

    return output_path


@app.route('/')
def index():
    """Serve the URL generator UI from static index.html"""
    if not INDEX_HTML.exists():
        return jsonify({'error': f'index.html not found at {INDEX_HTML}'}), 500
    return send_file(INDEX_HTML, mimetype='text/html')


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
