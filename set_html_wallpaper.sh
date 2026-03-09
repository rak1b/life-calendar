#!/bin/bash
# Convert `lifecalendar.html` → PNG and set it as wallpaper on Linux Mint.
#
# Why this exists:
# - You use it in crontab (@reboot / daily) to refresh your wallpaper on this PC.
# - Uses headless Chromium/Chrome to render the HTML exactly like the API does.
#
# Usage:
#   ./set_html_wallpaper.sh
#
# Optional env vars:
#   WIDTH=1920 HEIGHT=1080 OUTPUT=/path/to/out.png ./set_html_wallpaper.sh
#
# Notes:
# - Requires a Chromium/Chrome browser available on PATH.
# - Requires `Pillow` to fix the occasional bottom strip (optional but recommended).

set -euo pipefail

BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HTML_FILE="${BASE_DIR}/lifecalendar.html"

WIDTH_IN="${WIDTH:-}"
HEIGHT_IN="${HEIGHT:-}"
WIDTH="${WIDTH_IN:-1920}"
HEIGHT="${HEIGHT_IN:-1080}"
OUTPUT="${OUTPUT:-${BASE_DIR}/lifecalendar_wallpaper.png}"
SCREENSHOT_SCALE="${SCREENSHOT_SCALE:-2}"

if [[ ! -f "$HTML_FILE" ]]; then
  echo "Error: HTML file not found: $HTML_FILE" >&2
  exit 1
fi

# Find a browser
if command -v chromium >/dev/null 2>&1; then
  BROWSER="chromium"
elif command -v google-chrome >/dev/null 2>&1; then
  BROWSER="google-chrome"
elif command -v chromium-browser >/dev/null 2>&1; then
  BROWSER="chromium-browser"
elif command -v chrome >/dev/null 2>&1; then
  BROWSER="chrome"
else
  echo "Error: No Chromium/Chrome found on PATH." >&2
  echo "Install one of: chromium, chromium-browser, google-chrome" >&2
  exit 1
fi

echo "Rendering $HTML_FILE → $OUTPUT (${WIDTH}x${HEIGHT}) using $BROWSER"

# If WIDTH/HEIGHT were not provided explicitly, try to use current monitor size.
if [[ -z "$WIDTH_IN" || -z "$HEIGHT_IN" ]]; then
  if command -v xrandr >/dev/null 2>&1; then
    current_mode="$(xrandr 2>/dev/null | awk '/\*/ {print $1; exit}')"
    if [[ "$current_mode" =~ ^([0-9]+)x([0-9]+)$ ]]; then
      WIDTH="${BASH_REMATCH[1]}"
      HEIGHT="${BASH_REMATCH[2]}"
      echo "Detected display resolution: ${WIDTH}x${HEIGHT}"
    fi
  fi
fi

# Render HTML → PNG (high-res capture for cleaner output)
tmp_capture="$(mktemp --suffix=.png)"
"$BROWSER" \
  --headless \
  --no-sandbox \
  --disable-gpu \
  --disable-dev-shm-usage \
  --disable-software-rasterizer \
  --hide-scrollbars \
  --disable-web-security \
  --disable-features=VizDisplayCompositor \
  --window-size="${WIDTH},${HEIGHT}" \
  --force-device-scale-factor="${SCREENSHOT_SCALE}" \
  --screenshot="${tmp_capture}" \
  --virtual-time-budget=3000 \
  "file://${HTML_FILE}" >/dev/null 2>&1 || true

if [[ ! -f "$tmp_capture" ]]; then
  echo "Error: Failed to generate wallpaper image." >&2
  exit 1
fi

# Downscale + robust bottom-strip fix.
python3 - "$tmp_capture" "$OUTPUT" "$WIDTH" "$HEIGHT" <<'PY' || true
import sys
import os
from PIL import Image, ImageFilter

capture_path = sys.argv[1]
output = sys.argv[2]
width = int(sys.argv[3])
height = int(sys.argv[4])

if not capture_path or not os.path.exists(capture_path):
    raise SystemExit(0)

img = Image.open(capture_path).convert("RGBA")
if img.size != (width, height):
    resample = getattr(Image, "Resampling", Image)
    lanczos = getattr(resample, "LANCZOS", Image.LANCZOS)
    img = img.resize((width, height), lanczos)
    img = img.filter(ImageFilter.UnsharpMask(radius=0.8, percent=120, threshold=2))

def is_artifact_row(im, y):
    samples = []
    step = max(1, width // 40)
    for x in range(0, width, step):
        r, g, b, _a = im.getpixel((x, y))
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

strip_start = height
scan_depth = max(200, height // 3)
for y in range(height - 1, max(0, height - scan_depth), -1):
    if is_artifact_row(img, y):
        strip_start = y
    else:
        break

if strip_start < height:
    good_row = max(0, strip_start - 1)
    for y in range(strip_start, height):
        for x in range(width):
            img.putpixel((x, y), img.getpixel((x, good_row)))
    img.save(output, "PNG", optimize=True, compress_level=2)
else:
    img.save(output, "PNG", optimize=True, compress_level=2)
PY
rm -f "$tmp_capture"

if [[ ! -f "$OUTPUT" ]]; then
  echo "Error: Failed to save wallpaper image at: $OUTPUT" >&2
  exit 1
fi

# Set wallpaper (Mint / Cinnamon default)
desktop_env="$(echo "${XDG_CURRENT_DESKTOP:-}" | tr '[:upper:]' '[:lower:]')"

if [[ "$desktop_env" == *"cinnamon"* ]]; then
  gsettings set org.cinnamon.desktop.background picture-uri "file://${OUTPUT}"
  gsettings set org.cinnamon.desktop.background picture-options "zoom"
elif [[ "$desktop_env" == *"mate"* ]]; then
  gsettings set org.mate.background picture-filename "${OUTPUT}"
elif [[ "$desktop_env" == *"xfce"* ]]; then
  xfconf-query -c xfce4-desktop -p /backdrop/screen0/monitor0/workspace0/last-image -s "${OUTPUT}"
else
  # GNOME fallback
  gsettings set org.gnome.desktop.background picture-uri "file://${OUTPUT}" || true
fi

echo "Wallpaper set: ${OUTPUT}"
