#!/usr/bin/env python3
"""
Life Calendar API Server
Generates responsive calendar wallpapers for different device sizes
"""

from flask import Flask, send_file, request, jsonify
from flask_cors import CORS
import subprocess
import os
import tempfile
import shutil
from pathlib import Path
import json

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


def find_browser():
    """Find available Chromium/Chrome browser"""
    browsers = ['chromium', 'google-chrome', 'chromium-browser', 'chrome']
    for browser in browsers:
        if shutil.which(browser):
            return browser
    return None


def generate_image(html_path, output_path, width, height):
    """Generate PNG image from HTML using headless Chrome"""
    browser = find_browser()
    if not browser:
        raise RuntimeError("No Chromium/Chrome browser found. Please install chromium-browser.")
    
    html_uri = f"file://{html_path.absolute()}"
    
    cmd = [
        browser,
        '--headless',
        '--disable-gpu',
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


@app.route('/')
def index():
    """API documentation"""
    return jsonify({
        'name': 'Life Calendar API',
        'version': '1.0.0',
        'endpoints': {
            '/api/generate': {
                'method': 'GET',
                'description': 'Generate calendar wallpaper image',
                'parameters': {
                    'device': f"Device type: {', '.join(DEVICE_PRESETS.keys())}",
                    'width': 'Custom width in pixels (optional)',
                    'height': 'Custom height in pixels (optional)',
                    'format': 'Response format: image (default) or json'
                },
                'examples': [
                    '/api/generate?device=mobile',
                    '/api/generate?width=390&height=844',
                    '/api/generate?device=desktop&format=json'
                ]
            },
            '/api/presets': {
                'method': 'GET',
                'description': 'Get available device presets'
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
    try:
        # Get parameters
        device = request.args.get('device', 'desktop')
        width = request.args.get('width', type=int)
        height = request.args.get('height', type=int)
        format_type = request.args.get('format', 'image')
        
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
        
        # Create temporary output file
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:
            output_path = tmp_file.name
        
        # Generate image
        generate_image(HTML_FILE, output_path, dimensions['width'], dimensions['height'])
        
        if format_type == 'json':
            # Return JSON with file info
            file_size = os.path.getsize(output_path)
            return jsonify({
                'success': True,
                'device': device,
                'dimensions': dimensions,
                'file_size': file_size,
                'file_path': output_path,
                'message': 'Image generated successfully. Use /api/download/<filename> to download.'
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
    
    app.run(host='0.0.0.0', port=5000, debug=True)
