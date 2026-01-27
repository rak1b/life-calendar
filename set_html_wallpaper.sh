#!/bin/bash
# Simple script to convert HTML to wallpaper image and set it

HTML_FILE="$(cd "$(dirname "$0")" && pwd)/lifecalendar.html"
OUTPUT_IMAGE="$(cd "$(dirname "$0")" && pwd)/lifecalendar_wallpaper.png"

# Find browser
if command -v chromium &> /dev/null; then
    BROWSER="chromium"
elif command -v google-chrome &> /dev/null; then
    BROWSER="google-chrome"
elif command -v chromium-browser &> /dev/null; then
    BROWSER="chromium-browser"
else
    echo "Installing chromium-browser..."
    sudo apt install -y chromium-browser
    BROWSER="chromium-browser"
fi

# Convert HTML to PNG with additional flags to prevent white space
"$BROWSER" --headless --disable-gpu --window-size=1920,1080 \
    --hide-scrollbars --disable-web-security --disable-features=VizDisplayCompositor \
    --screenshot="$OUTPUT_IMAGE" \
    --virtual-time-budget=3000 \
    "file://$HTML_FILE" 2>/dev/null

if [ -f "$OUTPUT_IMAGE" ]; then
    # Fix any solid color strip at bottom by extending the gradient
    python3 -c "
from PIL import Image
img = Image.open('$OUTPUT_IMAGE')
width, height = img.size

# Find where problematic strip starts (solid white or black rows)
def is_solid_row(img, y, width):
    first_pixel = img.getpixel((width//2, y))
    # Check if it's pure white or pure black
    if first_pixel == (255, 255, 255) or first_pixel == (0, 0, 0):
        return True
    # Check if row is uniform (solid color)
    for x in range(0, width, 50):
        if img.getpixel((x, y)) != first_pixel:
            return False
    return True

# Find start of solid strip from bottom
strip_start = height
for y in range(height-1, height-200, -1):
    if is_solid_row(img, y, width):
        strip_start = y
    else:
        break

if strip_start < height:
    # Get colors from the last good row (strip_start - 1)
    good_row = max(0, strip_start - 1)
    for y in range(strip_start, height):
        for x in range(width):
            # Copy pixel from the good row above
            img.putpixel((x, y), img.getpixel((x, good_row)))
    img.save('$OUTPUT_IMAGE')
    print(f'Fixed strip from row {strip_start}')
else:
    print('No strip detected')
" 2>/dev/null || echo "PIL not available, skipping fix"
    
    # Set wallpaper
    gsettings set org.cinnamon.desktop.background picture-uri "file://$OUTPUT_IMAGE"
    gsettings set org.cinnamon.desktop.background picture-options 'stretched'
    echo "Wallpaper set: $OUTPUT_IMAGE"
else
    echo "Error: Failed to generate wallpaper"
    exit 1
fi
