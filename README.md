# Life Calendar Wallpaper Generator

A minimalist wallpaper generator for Linux Mint that creates beautiful, modern wallpapers showing your life progress in weeks or year progress.

## Features

- **Life Calendar**: Visualize your entire life in weeks (default: 90 years)
- **Year Calendar**: Track the current year's progress in weeks
- **Automatic Updates**: Can be scheduled to update daily
- **Customizable**: Adjust colors, sizes, and dimensions
- **Linux Mint Compatible**: Works with Cinnamon, MATE, and XFCE desktop environments

## Installation

### 1. Install Python Dependencies

```bash
pip3 install -r requirements.txt
```

Or install Pillow directly:

```bash
pip3 install Pillow
```

### 2. Make Script Executable (Optional)

```bash
chmod +x lifecalender.py
```

## Usage

### Basic Usage

Generate both Life Calendar and Year Calendar:

```bash
python3 lifecalender.py --birth-date 1990-01-15
```

Generate only Life Calendar:

```bash
python3 lifecalender.py --type life --birth-date 1990-01-15 --set-wallpaper
```

Generate only Year Calendar:

```bash
python3 lifecalender.py --type year --set-wallpaper
```

### Command Line Options

- `--type`: Choose `life`, `year`, or `both` (default: `both`)
- `--birth-date`: Your birth date in `YYYY-MM-DD` format (required for life calendar)
- `--output-dir`: Directory to save wallpapers (default: current directory)
- `--width`: Wallpaper width in pixels (default: 1920)
- `--height`: Wallpaper height in pixels (default: 1080)
- `--set-wallpaper`: Automatically set the generated wallpaper
- `--life-output`: Filename for life calendar (default: `life_calendar.png`)
- `--year-output`: Filename for year calendar (default: `year_calendar.png`)

### Examples

**Generate and set Life Calendar wallpaper:**

```bash
python3 lifecalender.py --type life --birth-date 1990-01-15 --set-wallpaper
```

**Generate custom resolution wallpaper:**

```bash
python3 lifecalender.py --birth-date 1990-01-15 --width 2560 --height 1440
```

**Generate to specific directory:**

```bash
python3 lifecalender.py --birth-date 1990-01-15 --output-dir ~/Pictures/wallpapers
```

## Automatic Updates

To automatically update your wallpaper daily, you can set up a cron job:

### Using Cron

1. Open your crontab:

```bash
crontab -e
```

2. Add a line to update the wallpaper daily at a specific time (e.g., midnight):

```bash
0 0 * * * /usr/bin/python3 /media/rakib/Projects/Life\ calender/lifecalender.py --type year --set-wallpaper
```

Or update both calendars:

```bash
0 0 * * * /usr/bin/python3 /media/rakib/Projects/Life\ calender/lifecalender.py --birth-date 1990-01-15 --set-wallpaper
```

**Note**: Replace the path and birth date with your actual values.

### Using Systemd Timer (Alternative)

You can also create a systemd user timer for more control. Create a service file and timer file in `~/.config/systemd/user/`.

## Customization

You can customize the appearance by editing the `LifeCalendarGenerator` class in `lifecalender.py`:

- `bg_color`: Background color (default: dark gray `(18, 18, 18)`)
- `filled_color`: Color for completed weeks (default: white `(255, 255, 255)`)
- `empty_color`: Color for remaining weeks (default: dark gray `(40, 40, 40)`)
- `dot_size`: Size of each dot in pixels (default: 8)
- `spacing`: Space between dots (default: 12)

## Troubleshooting

### Wallpaper Not Setting

- Make sure `gsettings` is installed: `sudo apt install gsettings`
- Check your desktop environment: `echo $XDG_CURRENT_DESKTOP`
- Try setting manually: Right-click on the generated image → Set as Wallpaper

### Font Issues

The script tries to use system fonts (DejaVu or Liberation). If fonts look wrong, you can:
- Install fonts: `sudo apt install fonts-dejavu fonts-liberation`
- Or modify the font paths in the code

### Permission Errors

If you get permission errors when setting wallpaper:
- Make sure the image file is readable
- Check that `gsettings` has proper permissions

## License

Free to use and modify as needed.


python3 lifecalender.py   --type year   --year-start 2025-12-01   --year-end 2026-05-31   --title "180 Days"   --set-wallpaper


# On startup
@reboot cd "/media/rakib/Projects/Life calender" && /usr/bin/python3 lifecalender.py --type year --year-start 2025-12-01 --year-end 2026-05-31 --title "180 Days" --set-wallpaper >> /home/rakib/.lifecalendar-cron.log 2>&1