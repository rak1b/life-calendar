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


# UI HTML template for URL generation — beautiful animated glassmorphism design
UI_HTML = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Life Calendar</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
    <style>
        /* ======= RESET ======= */
        *, *::before, *::after { margin: 0; padding: 0; box-sizing: border-box; }

        /* ======= DYNAMIC HUE — shifts smoothly over 30s ======= */
        @property --hue {
            syntax: "<number>";
            initial-value: 250;
            inherits: true;
        }
        @keyframes hueShift { 0%{--hue:250} 25%{--hue:310} 50%{--hue:190} 75%{--hue:30} 100%{--hue:250} }

        :root {
            animation: hueShift 30s ease-in-out infinite;
            /* all accent colours derive from the rotating hue */
            --accent-h: var(--hue);
            --accent: hsl(var(--accent-h) 72% 62%);
            --accent-soft: hsl(var(--accent-h) 60% 72%);
            --accent-glow: hsla(var(--accent-h) 80% 55% / .35);
            --accent-bg: hsla(var(--accent-h) 80% 55% / .12);
            --glass: rgba(16, 16, 24, .55);
            --glass-border: rgba(255, 255, 255, .07);
            --glass-highlight: rgba(255, 255, 255, .04);
            --text-1: #f0f0f5;
            --text-2: #a0a0b8;
            --text-3: #6a6a82;
            --surface: rgba(22, 22, 35, .7);
            --success: #34d399;
            --radius: 16px;
        }

        /* ======= BODY ======= */
        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background: #08080e;
            color: var(--text-1);
            min-height: 100dvh;
            overflow-x: hidden;
            display: flex;
            flex-direction: column;
            align-items: center;
            -webkit-font-smoothing: antialiased;
        }

        /* ======= ANIMATED BACKGROUND ======= */
        .bg { position: fixed; inset: 0; z-index: 0; overflow: hidden; pointer-events: none; }

        /* Slow-moving orbs that inherit the shifting hue */
        .orb {
            position: absolute;
            border-radius: 50%;
            filter: blur(100px);
            opacity: .45;
            animation: float 22s ease-in-out infinite alternate;
        }
        .orb-1 { width: 55vmax; height: 55vmax; top: -20%; left: -15%; background: hsla(var(--accent-h) 80% 55% / .3); animation-duration: 20s; }
        .orb-2 { width: 45vmax; height: 45vmax; bottom: -15%; right: -10%; background: hsla(calc(var(--accent-h)+60) 70% 50% / .25); animation-duration: 26s; animation-delay: -5s; }
        .orb-3 { width: 35vmax; height: 35vmax; top: 40%; left: 55%; background: hsla(calc(var(--accent-h)+140) 65% 55% / .2); animation-duration: 30s; animation-delay: -10s; }

        @keyframes float {
            0%   { transform: translate(0, 0) scale(1); }
            50%  { transform: translate(3vw, -4vh) scale(1.08); }
            100% { transform: translate(-2vw, 3vh) scale(.95); }
        }

        /* Subtle noise overlay */
        .noise {
            position: fixed; inset: 0; z-index: 1; pointer-events: none; opacity: .035;
            background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='.85' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E");
        }

        /* ======= MAIN CONTENT ======= */
        .page { position: relative; z-index: 2; width: 100%; max-width: 540px; padding: 20px 16px 40px; }

        /* ---- HEADER ---- */
        .header { text-align: center; padding: 28px 0 24px; }
        .header h1 {
            font-size: clamp(1.6rem, 5vw, 2rem);
            font-weight: 700;
            letter-spacing: -.02em;
            background: linear-gradient(135deg, var(--text-1), var(--accent-soft));
            -webkit-background-clip: text; background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .header p { color: var(--text-3); font-size: 13px; margin-top: 6px; }

        /* ---- GLASS CARD ---- */
        .card {
            background: var(--glass);
            backdrop-filter: blur(24px); -webkit-backdrop-filter: blur(24px);
            border: 1px solid var(--glass-border);
            border-radius: var(--radius);
            padding: 22px 20px;
            margin-bottom: 16px;
            box-shadow: 0 8px 32px rgba(0,0,0,.25), inset 0 1px 0 var(--glass-highlight);
            transition: border-color .4s;
        }
        .card:hover { border-color: var(--accent-glow); }
        .card-title {
            font-size: 11px; font-weight: 600; text-transform: uppercase;
            letter-spacing: 1.2px; color: var(--accent-soft); margin-bottom: 14px;
            display: flex; align-items: center; gap: 6px;
        }
        .card-title svg { width: 14px; height: 14px; stroke: var(--accent-soft); fill: none; stroke-width: 2; }

        /* ---- FORM ELEMENTS ---- */
        .form-group { margin-bottom: 14px; }
        label { display: block; font-size: 12px; font-weight: 500; color: var(--text-2); margin-bottom: 5px; }
        input, select {
            width: 100%; padding: 11px 13px;
            font-family: inherit; font-size: 14px;
            background: var(--surface); color: var(--text-1);
            border: 1px solid var(--glass-border); border-radius: 10px;
            transition: border-color .25s, box-shadow .25s;
            -webkit-appearance: none; appearance: none;
        }
        select { background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' fill='%236a6a82' viewBox='0 0 16 16'%3E%3Cpath d='M8 11L3 6h10z'/%3E%3C/svg%3E"); background-repeat: no-repeat; background-position: right 12px center; padding-right: 32px; }
        input:focus, select:focus { outline: none; border-color: var(--accent); box-shadow: 0 0 0 3px var(--accent-glow); }
        /* Fix date input for dark theme */
        input[type="date"]::-webkit-calendar-picker-indicator { filter: invert(.7); }

        .row { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }

        /* ---- PRESET PILLS ---- */
        .presets { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 10px; }
        .pill {
            padding: 7px 14px; font-size: 12px; font-weight: 500;
            background: var(--surface); color: var(--text-2);
            border: 1px solid var(--glass-border); border-radius: 20px;
            cursor: pointer; transition: all .25s; user-select: none;
        }
        .pill:hover, .pill.active {
            background: var(--accent-bg); color: var(--accent-soft);
            border-color: var(--accent); box-shadow: 0 0 12px var(--accent-glow);
        }

        /* ---- URL OUTPUT ---- */
        .url-box {
            background: var(--surface); border: 1px solid var(--glass-border);
            border-radius: 10px; padding: 13px 14px; margin-bottom: 14px;
            font-family: 'JetBrains Mono', monospace; font-size: 11.5px; line-height: 1.6;
            color: var(--accent-soft); word-break: break-all; min-height: 52px;
            transition: border-color .3s;
        }
        .url-box:hover { border-color: var(--accent); }

        /* ---- BUTTONS ---- */
        .btn {
            display: inline-flex; align-items: center; justify-content: center; gap: 8px;
            width: 100%; padding: 13px 18px;
            font-family: inherit; font-size: 14px; font-weight: 600;
            border: none; border-radius: 10px; cursor: pointer;
            transition: all .25s; position: relative; overflow: hidden;
        }
        .btn svg { width: 16px; height: 16px; stroke: currentColor; fill: none; stroke-width: 2; flex-shrink: 0; }

        .btn-accent {
            background: linear-gradient(135deg, var(--accent), var(--accent-soft));
            color: #fff; box-shadow: 0 4px 20px var(--accent-glow);
        }
        .btn-accent:hover { transform: translateY(-2px); box-shadow: 0 8px 30px var(--accent-glow); }
        .btn-accent:active { transform: translateY(0); }

        .btn-glass {
            background: var(--surface); color: var(--text-1);
            border: 1px solid var(--glass-border);
        }
        .btn-glass:hover { border-color: var(--accent); background: var(--accent-bg); }

        .btn-row { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }

        /* ---- COLLAPSIBLE SECTION ---- */
        .collapse-toggle {
            display: flex; align-items: center; justify-content: space-between;
            width: 100%; padding: 0; border: none; background: none;
            cursor: pointer; color: var(--accent-soft); font-size: 11px; font-weight: 600;
            text-transform: uppercase; letter-spacing: 1.2px; font-family: inherit;
        }
        .collapse-toggle svg { transition: transform .3s; }
        .collapse-toggle.open svg { transform: rotate(180deg); }
        .collapse-body { max-height: 0; overflow: hidden; transition: max-height .4s ease; }
        .collapse-body.open { max-height: 800px; }
        .collapse-inner { padding-top: 16px; }

        /* ---- GUIDE STEPS ---- */
        .steps { counter-reset: step; display: flex; flex-direction: column; gap: 14px; }
        .step {
            display: flex; gap: 12px; font-size: 13px; line-height: 1.55; color: var(--text-2);
        }
        .step::before {
            counter-increment: step; content: counter(step);
            display: flex; align-items: center; justify-content: center;
            min-width: 26px; height: 26px; border-radius: 8px; flex-shrink: 0;
            font-size: 12px; font-weight: 700;
            background: var(--accent-bg); color: var(--accent-soft);
            border: 1px solid var(--accent-glow);
        }
        .step code {
            display: inline-block; padding: 2px 6px; border-radius: 4px;
            background: var(--surface); font-family: 'JetBrains Mono', monospace; font-size: 11px;
            color: var(--accent-soft);
        }

        /* ---- TOAST ---- */
        .toast {
            position: fixed; bottom: 28px; left: 50%;
            transform: translateX(-50%) translateY(80px);
            background: var(--success); color: #fff;
            padding: 11px 22px; border-radius: 10px;
            font-size: 13px; font-weight: 600; opacity: 0;
            transition: all .35s cubic-bezier(.4,0,.2,1); z-index: 200;
            box-shadow: 0 4px 20px rgba(52, 211, 153, .35);
        }
        .toast.show { opacity: 1; transform: translateX(-50%) translateY(0); }

        /* ---- FOOTER ---- */
        .footer { text-align: center; padding: 18px 0 8px; color: var(--text-3); font-size: 11px; }
        .footer a { color: var(--accent-soft); text-decoration: none; }
        .footer a:hover { text-decoration: underline; }

        /* ======= RESPONSIVE — fully mobile-first ======= */
        @media (max-width: 480px) {
            .page { padding: 12px 10px 32px; }
            .card { padding: 18px 14px; margin-bottom: 12px; }
            .header { padding: 20px 0 18px; }
            .header h1 { font-size: 1.4rem; }
            .btn { padding: 12px 14px; font-size: 13px; }
            .url-box { font-size: 10.5px; padding: 11px 10px; }
            .row { gap: 8px; }
            .btn-row { grid-template-columns: 1fr; }
        }
        @media (max-width: 360px) {
            .card { padding: 14px 10px; border-radius: 12px; }
            .presets { gap: 6px; }
            .pill { padding: 5px 10px; font-size: 11px; }
        }
        @media (min-width: 768px) {
            .page { padding: 32px 24px 48px; }
            .card { padding: 28px 26px; }
        }
    </style>
</head>
<body>

<!-- Animated background -->
<div class="bg">
    <div class="orb orb-1"></div>
    <div class="orb orb-2"></div>
    <div class="orb orb-3"></div>
</div>
<div class="noise"></div>

<main class="page">

    <!-- Header -->
    <div class="header">
        <h1>Life Calendar</h1>
        <p>Generate wallpapers &amp; auto-update on mobile</p>
    </div>

    <!-- Date Range Card -->
    <div class="card">
        <div class="card-title">
            <svg viewBox="0 0 24 24"><rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>
            Date Range
        </div>
        <div class="row">
            <div class="form-group">
                <label>Start Date</label>
                <input type="date" id="startDate" value="2025-12-01">
            </div>
            <div class="form-group">
                <label>End Date</label>
                <input type="date" id="endDate" value="2026-05-31">
            </div>
        </div>
        <div class="form-group">
            <label>Title</label>
            <input type="text" id="title" value="180 DAYS" placeholder="e.g. 180 DAYS">
        </div>
        <div class="presets">
            <button class="pill" data-days="30">30 Days</button>
            <button class="pill" data-days="60">60 Days</button>
            <button class="pill" data-days="90">90 Days</button>
            <button class="pill active" data-days="180">180 Days</button>
            <button class="pill" data-days="365">1 Year</button>
        </div>
    </div>

    <!-- Device Card -->
    <div class="card">
        <div class="card-title">
            <svg viewBox="0 0 24 24"><rect x="5" y="2" width="14" height="20" rx="2"/><line x1="12" y1="18" x2="12.01" y2="18"/></svg>
            Device
        </div>
        <div class="form-group">
            <label>Screen Size</label>
            <select id="device">
                <option value="mobile">Mobile — 390 × 844</option>
                <option value="mobile-large">Mobile Large — 428 × 926</option>
                <option value="tablet">Tablet — 768 × 1024</option>
                <option value="tablet-landscape">Tablet Landscape — 1024 × 768</option>
                <option value="desktop">Desktop — 1920 × 1080</option>
                <option value="desktop-4k">Desktop 4K — 3840 × 2160</option>
                <option value="custom">Custom Size…</option>
            </select>
        </div>
        <div class="row" id="customSize" style="display:none;">
            <div class="form-group">
                <label>Width (px)</label>
                <input type="number" id="width" value="390" min="100" max="8000">
            </div>
            <div class="form-group">
                <label>Height (px)</label>
                <input type="number" id="height" value="844" min="100" max="8000">
            </div>
        </div>
    </div>

    <!-- Generated URL Card -->
    <div class="card">
        <div class="card-title">
            <svg viewBox="0 0 24 24"><path d="M10 13a5 5 0 007.54.54l3-3a5 5 0 00-7.07-7.07l-1.72 1.71"/><path d="M14 11a5 5 0 00-7.54-.54l-3 3a5 5 0 007.07 7.07l1.71-1.71"/></svg>
            Generated URL
        </div>
        <div class="url-box" id="urlOutput">Configure above, then tap Generate</div>
        <div class="btn-row">
            <button class="btn btn-accent" onclick="generateUrl()">
                <svg viewBox="0 0 24 24"><path d="M10 13a5 5 0 007.54.54l3-3a5 5 0 00-7.07-7.07l-1.72 1.71"/><path d="M14 11a5 5 0 00-7.54-.54l-3 3a5 5 0 007.07 7.07l1.71-1.71"/></svg>
                Generate
            </button>
            <button class="btn btn-glass" onclick="copyUrl()">
                <svg viewBox="0 0 24 24"><rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1"/></svg>
                Copy
            </button>
        </div>
    </div>

    <!-- Download Button -->
    <button class="btn btn-accent" onclick="openUrl()" style="margin-bottom:16px;">
        <svg viewBox="0 0 24 24"><path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
        Download Image
    </button>

    <!-- Auto-Update Guide (collapsible) -->
    <div class="card">
        <button class="collapse-toggle" id="guideToggle" onclick="toggleGuide()">
            <span style="display:flex;align-items:center;gap:6px;">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M12 16v-4"/><path d="M12 8h.01"/></svg>
                Auto-Update on Mobile (MacroDroid)
            </span>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="6 9 12 15 18 9"/></svg>
        </button>
        <div class="collapse-body" id="guideBody">
            <div class="collapse-inner">
                <div class="steps">
                    <div class="step">Install <strong>MacroDroid</strong> from Play Store (free).</div>
                    <div class="step">Create a new Macro → <strong>Trigger</strong>: Day/Time → set <code>Every Day</code> at a time you prefer (e.g. 6:00 AM).</div>
                    <div class="step"><strong>Action</strong> → choose <strong>HTTP Request (GET)</strong> → paste your Generated URL above.</div>
                    <div class="step">Set <strong>Save response to file</strong> → pick a path like <code>/sdcard/Pictures/calendar.png</code>.</div>
                    <div class="step">Add another <strong>Action</strong> → <strong>Set Wallpaper</strong> → select the saved file path.</div>
                    <div class="step">Save the Macro. Your wallpaper will now <strong>update itself every day</strong> automatically!</div>
                </div>
                <p style="margin-top:14px; font-size:12px; color:var(--text-3); line-height:1.5;">
                    <strong style="color:var(--accent-soft);">Tip:</strong> The image is regenerated on each request, so the calendar progress updates automatically.
                    You can also use <strong>Tasker</strong> or <strong>Automate</strong> with the same URL.
                </p>
            </div>
        </div>
    </div>

    <div class="footer">
        <p><a href="/api/docs">API Docs</a> · <a href="/health">Health</a></p>
    </div>
</main>

<div class="toast" id="toast"></div>

<script>
    const baseUrl = window.location.origin;
    let generatedUrl = '';

    /* ---- Preset pills ---- */
    document.querySelectorAll('.pill').forEach(btn => {
        btn.addEventListener('click', function () {
            document.querySelectorAll('.pill').forEach(b => b.classList.remove('active'));
            this.classList.add('active');
            const days = parseInt(this.dataset.days);
            const today = new Date();
            const end = new Date(today);
            end.setDate(end.getDate() + days);
            document.getElementById('startDate').value = fmt(today);
            document.getElementById('endDate').value = fmt(end);
            document.getElementById('title').value = days + ' DAYS';
            generateUrl();
        });
    });

    /* ---- Device select ---- */
    document.getElementById('device').addEventListener('change', function () {
        document.getElementById('customSize').style.display = this.value === 'custom' ? 'grid' : 'none';
        generateUrl();
    });

    /* ---- Auto-generate on every input change ---- */
    document.querySelectorAll('input, select').forEach(el => el.addEventListener('input', generateUrl));

    /* ---- Helper: format date as YYYY-MM-DD ---- */
    function fmt(d) { return d.toISOString().split('T')[0]; }

    /* ---- Build URL ---- */
    function generateUrl() {
        const start  = document.getElementById('startDate').value;
        const end    = document.getElementById('endDate').value;
        const title  = encodeURIComponent(document.getElementById('title').value);
        const device = document.getElementById('device').value;
        let url = `${baseUrl}/api/generate?start=${start}&end=${end}&title=${title}`;
        if (device === 'custom') {
            url += `&width=${document.getElementById('width').value}&height=${document.getElementById('height').value}`;
        } else {
            url += `&device=${device}`;
        }
        generatedUrl = url;
        document.getElementById('urlOutput').textContent = url;
    }

    /* ---- Copy to clipboard ---- */
    function copyUrl() {
        if (!generatedUrl) generateUrl();
        navigator.clipboard.writeText(generatedUrl).then(() => {
            toast('Copied to clipboard!');
        }).catch(() => {
            // Fallback for older browsers / non-HTTPS
            const ta = document.createElement('textarea');
            ta.value = generatedUrl; document.body.appendChild(ta);
            ta.select(); document.execCommand('copy');
            document.body.removeChild(ta);
            toast('Copied to clipboard!');
        });
    }

    /* ---- Open / download ---- */
    function openUrl() {
        if (!generatedUrl) generateUrl();
        window.open(generatedUrl, '_blank');
    }

    /* ---- Collapsible guide ---- */
    function toggleGuide() {
        document.getElementById('guideToggle').classList.toggle('open');
        document.getElementById('guideBody').classList.toggle('open');
    }

    /* ---- Toast notification ---- */
    function toast(msg) {
        const el = document.getElementById('toast');
        el.textContent = msg; el.classList.add('show');
        setTimeout(() => el.classList.remove('show'), 2200);
    }

    /* ---- Init ---- */
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
