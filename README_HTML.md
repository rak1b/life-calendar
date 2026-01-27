# HTML/CSS/JS Life Calendar Wallpaper

This is a modern web-based version of the Life Calendar wallpaper with true neomorphic design effects.

## Features

- **True Neomorphic Design**: Uses CSS `box-shadow` for authentic soft UI effects
- **Modern CSS Gradients**: Smooth, animated background gradients
- **Responsive Design**: Adapts to different screen sizes
- **Real-time Updates**: JavaScript calculates dates dynamically
- **Better Visual Effects**: CSS supports blur, shadows, and animations that PIL cannot

## Setup

### Option 1: Use as HTML Wallpaper (Recommended)

1. **Install Chromium/Chrome** (if not already installed):
   ```bash
   sudo apt install chromium-browser
   ```

2. **Generate and set wallpaper**:
   ```bash
   ./set_html_wallpaper.sh
   ```

3. **Update the HTML file** to customize dates:
   - Edit `lifecalendar.html`
   - Modify the `config` object in the JavaScript section:
     ```javascript
     const config = {
         yearStart: '2025-12-01',
         yearEnd: '2026-05-31',
         title: '180 Days'
     };
     ```

### Option 2: Use with Web-based Wallpaper Tools

You can use tools like:
- **Plank** (for HTML wallpapers)
- **Variety** (supports HTML wallpapers)
- **Custom HTML wallpaper extensions**

### Option 3: Run as Fullscreen Web App

1. Open `lifecalendar.html` in a browser
2. Press F11 for fullscreen
3. Use browser extensions to set as wallpaper

## Advantages over Python/PIL

- ✅ **True Neomorphic Effects**: CSS `box-shadow` with blur support
- ✅ **Smooth Animations**: CSS animations and transitions
- ✅ **Better Gradients**: CSS gradient support is superior
- ✅ **Real-time Updates**: JavaScript updates dates automatically
- ✅ **Modern Design**: Access to all modern CSS features
- ✅ **Performance**: Hardware-accelerated rendering

## Customization

### Colors
Edit the `colorPalettes` array in the JavaScript section to change background colors.

### Neomorphic Effects
Modify the `.dot.filled` and `.dot.empty` CSS classes to adjust shadow effects:
```css
.dot.filled {
    box-shadow: 
        -3px -3px 8px rgba(255, 255, 255, 0.1),  /* Light shadow */
        3px 3px 8px rgba(0, 0, 0, 0.3),          /* Dark shadow */
        inset -1px -1px 2px rgba(255, 255, 255, 0.1),
        inset 1px 1px 2px rgba(0, 0, 0, 0.2);
}
```

### Dot Sizes
Adjust the `.dot` class width/height in CSS.

## Daily Auto-Update

Add to crontab to regenerate daily:
```bash
0 0 * * * cd "/media/rakib/Projects/Life calender" && ./set_html_wallpaper.sh
```
