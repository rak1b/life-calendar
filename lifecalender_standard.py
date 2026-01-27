#!/usr/bin/env python3
"""
Life Calendar Wallpaper Generator for Linux Mint
Generates minimalist wallpapers showing life progress in weeks or year progress.
"""

import os
import sys
import calendar
from datetime import datetime, date, timedelta
from PIL import Image, ImageDraw, ImageFont
import subprocess
import argparse
from pathlib import Path


class LifeCalendarGenerator:
    """Generate Life Calendar and Year Calendar wallpapers."""
    
    def __init__(self, width=1920, height=1080, dot_size=14, spacing=24, 
                 bg_color=(10, 10, 15), dot_color=(255, 255, 255),
                 filled_color=(255, 255, 255), empty_color=(40, 40, 40)):
        """
        Initialize the generator with customizable parameters.
        
        Args:
            width: Wallpaper width in pixels
            height: Wallpaper height in pixels
            dot_size: Size of each dot in pixels
            spacing: Space between dots in pixels
            bg_color: Background color (RGB tuple)
            dot_color: Color for filled dots (RGB tuple)
            filled_color: Color for completed weeks (RGB tuple)
            empty_color: Color for remaining weeks (RGB tuple)
        """
        self.width = width
        self.height = height
        self.dot_size = dot_size
        self.spacing = spacing
        self.bg_color = bg_color
        self.dot_color = dot_color
        self.filled_color = filled_color
        self.empty_color = empty_color
        
        # Base grid dimensions (max possible given the screen).
        # Specific calendar types can request their own grid (e.g. 52x90).
        self.cols = (width - 2 * spacing) // (dot_size + spacing)
        self.rows = (height - 2 * spacing) // (dot_size + spacing)
        
    def calculate_life_weeks(self, birth_date):
        """
        Calculate weeks lived and total weeks in expected lifespan.
        
        Args:
            birth_date: Date of birth (datetime.date object)
            
        Returns:
            Tuple of (weeks_lived, total_weeks, weeks_remaining, days_lived, total_days, days_remaining)
        """
        today = date.today()
        expected_lifespan_years = 90  # Average lifespan, can be customized
        total_weeks = expected_lifespan_years * 52
        total_days = expected_lifespan_years * 365
        
        days_lived = (today - birth_date).days
        weeks_lived = days_lived // 7
        weeks_remaining = total_weeks - weeks_lived
        days_remaining = total_days - days_lived
        
        return weeks_lived, total_weeks, weeks_remaining, days_lived, total_days, days_remaining
    
    def calculate_year_weeks(self, start_date=None, end_date=None):
        """
        Calculate weeks elapsed and remaining in a period.
        
        Args:
            start_date: Start date of the period (datetime.date object). If None, uses Jan 1 of current year.
            end_date: End date of the period (datetime.date object). If None, uses Dec 31 of current year.
        
        Returns:
            Tuple of (weeks_elapsed, total_weeks, weeks_remaining, days_elapsed, total_days, days_remaining)
        """
        today = date.today()
        
        # Use custom dates if provided, otherwise use current year
        if start_date is None:
            period_start = date(today.year, 1, 1)
        else:
            period_start = start_date
            
        if end_date is None:
            period_end = date(today.year, 12, 31)
        else:
            period_end = end_date
        
        # Calculate total days and weeks in the period
        total_days = (period_end - period_start).days + 1  # Include both start and end days
        total_weeks = (total_days + 6) // 7  # Round up to include partial weeks
        
        # Calculate days and weeks elapsed
        if today < period_start:
            days_elapsed = 0
            weeks_elapsed = 0
        elif today > period_end:
            days_elapsed = total_days
            weeks_elapsed = total_weeks
        else:
            days_elapsed = (today - period_start).days + 1  # Include today
            weeks_elapsed = days_elapsed // 7
            
        # Cap at total
        if weeks_elapsed > total_weeks:
            weeks_elapsed = total_weeks
        if days_elapsed > total_days:
            days_elapsed = total_days
            
        weeks_remaining = total_weeks - weeks_elapsed
        days_remaining = total_days - days_elapsed
        
        return weeks_elapsed, total_weeks, weeks_remaining, days_elapsed, total_days, days_remaining
    
    def draw_grid(self, filled_count, total_count, title_text, subtitle_text,
                  grid_cols=None, grid_rows=None, start_date=None, end_date=None,
                  current_day_index=None, footer_text=None):
        """
        Draw the calendar grid with dots.
        
        Args:
            filled_count: Number of filled dots
            total_count: Total number of dots to show
            title_text: Title to display (single line)
            subtitle_text: (Unused in current minimal UI, kept for backward compatibility)
            footer_text: Optional text to show below the grid (e.g., \"64d left · 28%\")
            
        Returns:
            PIL Image object
        """
        # Create image with dark background
        img = Image.new('RGB', (self.width, self.height), self.bg_color)
        draw = ImageDraw.Draw(img)
        
        # Try to load a unique/modern font, fallback to alternatives
        title_font = None
        footer_font = None
        try:
            # Try unique modern fonts first (Montserrat, Poppins, Raleway, etc.)
            font_paths = [
                # Popular unique fonts
                "/usr/share/fonts/truetype/montserrat/Montserrat-Bold.ttf",
                "/usr/share/fonts/truetype/poppins/Poppins-Bold.ttf",
                "/usr/share/fonts/truetype/raleway/Raleway-Bold.ttf",
                "/usr/share/fonts/truetype/source-sans-pro/SourceSansPro-Bold.ttf",
                "/usr/share/fonts/truetype/work-sans/WorkSans-Bold.ttf",
                "/usr/share/fonts/truetype/inter/Inter-Bold.ttf",
                "/usr/share/fonts/truetype/roboto/Roboto-Bold.ttf",
                "/usr/share/fonts/truetype/ubuntu/Ubuntu-Bold.ttf",
                "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf",
            ]
            for font_path in font_paths:
                try:
                    # Slightly smaller, more minimal text
                    title_font = ImageFont.truetype(font_path, 20)
                    footer_font = ImageFont.truetype(font_path, 15)  # Smaller footer
                    break
                except:
                    continue
        except:
            pass
        
        # Fallback to default if no font found
        if title_font is None:
            try:
                title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 30)
                footer_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 20)
            except:
                title_font = ImageFont.load_default()
                footer_font = ImageFont.load_default()
        
        # Use footer_font if available, otherwise use title_font
        if footer_font is None:
            footer_font = title_font
        
        # Decide grid resolution. If specific grid sizes are provided,
        # use them (e.g. 52 weeks x 90 years). Otherwise, fall back to
        # the maximum grid that fits the screen.
        cols = grid_cols if grid_cols is not None else self.cols
        rows = grid_rows if grid_rows is not None else self.rows
        total_dots_to_show = min(total_count, cols * rows)
        # How many columns actually used given the number of dots
        used_cols = min(cols, total_dots_to_show) if total_dots_to_show > 0 else cols
        grid_width = used_cols * (self.dot_size + self.spacing) - self.spacing
        used_rows = (total_dots_to_show + cols - 1) // cols if total_dots_to_show > 0 else rows
        grid_height = used_rows * (self.dot_size + self.spacing) - self.spacing
        
        start_x = (self.width - grid_width) // 2
        # Center grid vertically
        start_y = (self.height - grid_height) // 2

        # For a cleaner, more minimal UI we no longer draw a card background.
        # Keep some virtual "card" bounds for aligning title/footer with the grid.
        card_left = start_x
        card_top = start_y
        card_right = start_x + grid_width
        card_bottom = start_y + grid_height
        
        # Draw title centered and close to the dots (aligned to card width)
        if title_text:
            title_bbox = draw.textbbox((0, 0), title_text, font=title_font)
            title_width = title_bbox[2] - title_bbox[0]
            title_height = title_bbox[3] - title_bbox[1]
            card_width = card_right - card_left
            title_x = card_left + (card_width - title_width) // 2
            # Position title just above the grid with a bit more breathing room
            # Increase this offset to create more margin between title and dots.
            title_y = max(10, card_top - title_height - 28)
            
            # Title in white with slight transparency effect (lighter white to simulate transparency)
            white_transparent = (200, 200, 200)  # ~78% opacity effect
            draw.text((title_x, title_y), title_text, fill=white_transparent, font=title_font)
        
        # Dot palette tuned for a cleaner, more modern look
        filled_dot = (230, 230, 230)     # soft white
        empty_dot = (55, 55, 55)         # dark gray
        today_dot = (70, 220, 140)       # mint green highlight
        today_ring = (30, 120, 75)       # darker ring for contrast

        # Draw dots
        dot_index = 0
        for row in range(rows):
            for col in range(cols):
                if dot_index >= total_dots_to_show:
                    break
                    
                x = start_x + col * (self.dot_size + self.spacing)
                y = start_y + row * (self.dot_size + self.spacing)
                
                # Determine if this dot should be filled
                if dot_index < filled_count:
                    # Highlight current day
                    if current_day_index is not None and dot_index == current_day_index:
                        # Draw a subtle ring/glow by drawing a slightly larger circle first
                        ring_pad = 3
                        draw.ellipse(
                            [x - ring_pad, y - ring_pad, x + self.dot_size + ring_pad, y + self.dot_size + ring_pad],
                            fill=today_ring,
                            outline=None
                        )
                        dot_color = today_dot
                    else:
                        dot_color = filled_dot
                else:
                    dot_color = empty_dot
                
                # Draw dot as a circle
                draw.ellipse(
                    [x, y, x + self.dot_size, y + self.dot_size],
                    fill=dot_color,
                    outline=None
                )
                
                dot_index += 1
            
            if dot_index >= total_dots_to_show:
                break

        # Draw footer text (e.g., \"64d left · 28%\") centered below the grid
        if footer_text:
            footer_bbox = draw.textbbox((0, 0), footer_text, font=footer_font)
            footer_width = footer_bbox[2] - footer_bbox[0]
            card_width = card_right - card_left
            footer_x = card_left + (card_width - footer_width) // 2
            # Slightly larger gap under the grid for footer readability
            footer_y = card_bottom + 28

            # Footer in white with slight transparency effect (lighter white to simulate transparency)
            white_transparent = (200, 200, 200)  # ~78% opacity effect
            draw.text((footer_x, footer_y), footer_text, fill=white_transparent, font=footer_font)
        
        return img
    
    def generate_life_calendar(self, birth_date, output_path, custom_title=None):
        """
        Generate Life Calendar wallpaper.
        
        Args:
            birth_date: Date of birth (datetime.date object)
            output_path: Path to save the generated image
        """
        weeks_lived, total_weeks, weeks_remaining, days_lived, total_days, days_remaining = self.calculate_life_weeks(birth_date)
        
        # Use custom title if provided, otherwise fallback to default
        title = custom_title or "Life Calendar"
        subtitle = ""  # No extra subtitle text in minimal UI
        
        # Use a 52 (weeks) x 90 (years) grid to mimic the classic Life Calendar look.
        img = self.draw_grid(
            weeks_lived,
            total_weeks,
            title,
            subtitle,
            grid_cols=52,
            grid_rows=90,
            start_date=None,
            end_date=None,
            current_day_index=None  # Life calendar uses weeks, not days
        )
        img.save(output_path, 'PNG')
        print(f"Life Calendar generated: {output_path}")
        print(f"Weeks lived: {weeks_lived:,} / {total_weeks:,} ({weeks_lived*100//total_weeks}%)")
        print(f"Days lived: {days_lived:,} / {total_days:,} ({days_lived*100//total_days}%)")
    
    def generate_year_calendar(self, output_path, start_date=None, end_date=None, custom_title=None):
        """
        Generate Year Calendar wallpaper.
        
        Args:
            output_path: Path to save the generated image
            start_date: Start date of the period (datetime.date object). If None, uses current year.
            end_date: End date of the period (datetime.date object). If None, uses current year.
        """
        weeks_elapsed, total_weeks, weeks_remaining, days_elapsed, total_days, days_remaining = self.calculate_year_weeks(start_date, end_date)
        
        # Minimal UI: only a single title line. Progress details are printed to console.
        if start_date and end_date:
            start_str = start_date.strftime("%b %d, %Y")
            end_str = end_date.strftime("%b %d, %Y")
            # If user does not provide a title, use a compact default including range.
            default_title = f"{start_str} → {end_str}"
        else:
            default_title = "Year Calendar"
        
        title = custom_title or default_title
        subtitle = ""  # No subtitle on the wallpaper
        
        # For the year/custom-range view, each dot represents ONE DAY.
        # Choose columns based on days to get a compact, readable grid.
        if total_days <= 31:
            # Up to one month: single row of days
            grid_cols = total_days
            grid_rows = 1
        else:
            # Use 31 columns (max days in month) and as many rows as needed
            grid_cols = 31
            grid_rows = (total_days + grid_cols - 1) // grid_cols  # Round up
        
        # Calculate current day index (0-based) for highlighting today's dot.
        # days_elapsed is 1-based (includes today), so current_day_index = days_elapsed - 1.
        current_day_index = days_elapsed - 1 if days_elapsed > 0 else None
        
        # Footer text: "Xd left · Y%" similar to the reference design.
        percent_done = days_elapsed * 100 // total_days if total_days > 0 else 0
        days_left = days_remaining
        footer_text = f"{days_left}d left · {percent_done}%"
        
        # IMPORTANT: dots represent DAYS, not weeks.
        img = self.draw_grid(
            days_elapsed,
            total_days,
            title,
            subtitle,
            grid_cols=grid_cols,
            grid_rows=grid_rows,
            start_date=start_date,
            end_date=end_date,
            current_day_index=current_day_index,
            footer_text=footer_text
        )
        img.save(output_path, 'PNG')
        print(f"Year Calendar generated: {output_path}")
        print(f"Weeks elapsed: {weeks_elapsed} / {total_weeks} ({weeks_elapsed*100//total_weeks if total_weeks > 0 else 0}%)")
        print(f"Days elapsed: {days_elapsed} / {total_days} ({days_elapsed*100//total_days if total_days > 0 else 0}%)")


def set_wallpaper_linux_mint(image_path):
    """
    Set wallpaper on Linux Mint using gsettings.
    Works with Cinnamon, MATE, and XFCE desktop environments.
    
    Args:
        image_path: Absolute path to the wallpaper image
    """
    # Convert to absolute path
    abs_path = os.path.abspath(image_path)
    
    if not os.path.exists(abs_path):
        print(f"Error: Image file not found: {abs_path}")
        return False
    
    # Detect desktop environment
    desktop_env = os.environ.get('XDG_CURRENT_DESKTOP', '').lower()
    
    try:
        if 'cinnamon' in desktop_env:
            # Cinnamon (default Linux Mint)
            subprocess.run([
                'gsettings', 'set',
                'org.cinnamon.desktop.background',
                'picture-uri',
                f"file://{abs_path}"
            ], check=True)
            subprocess.run([
                'gsettings', 'set',
                'org.cinnamon.desktop.background',
                'picture-options',
                'scaled'
            ], check=True)
            print(f"Wallpaper set successfully for Cinnamon: {abs_path}")
            
        elif 'mate' in desktop_env:
            # MATE
            subprocess.run([
                'gsettings', 'set',
                'org.mate.background',
                'picture-filename',
                abs_path
            ], check=True)
            print(f"Wallpaper set successfully for MATE: {abs_path}")
            
        elif 'xfce' in desktop_env:
            # XFCE
            subprocess.run([
                'xfconf-query', '-c', 'xfce4-desktop',
                '-p', '/backdrop/screen0/monitor0/workspace0/last-image',
                '-s', abs_path
            ], check=True)
            print(f"Wallpaper set successfully for XFCE: {abs_path}")
            
        else:
            # Try generic GNOME settings (fallback)
            subprocess.run([
                'gsettings', 'set',
                'org.gnome.desktop.background',
                'picture-uri',
                f"file://{abs_path}"
            ], check=True)
            print(f"Wallpaper set successfully (generic): {abs_path}")
            
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"Error setting wallpaper: {e}")
        print("Make sure gsettings is available and you have the right permissions.")
        return False
    except FileNotFoundError:
        print("Error: gsettings or xfconf-query not found. Please install gsettings or xfconf.")
        return False


def main():
    """Main function to handle command line arguments and generate wallpapers."""
    parser = argparse.ArgumentParser(
        description='Generate Life Calendar and Year Calendar wallpapers for Linux Mint'
    )
    parser.add_argument(
        '--type',
        choices=['life', 'year', 'both'],
        default='both',
        help='Type of calendar to generate (default: both)'
    )
    parser.add_argument(
        '--birth-date',
        type=str,
        help='Birth date in YYYY-MM-DD format (required for life calendar)'
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        default='.',
        help='Output directory for generated wallpapers (default: current directory)'
    )
    parser.add_argument(
        '--width',
        type=int,
        default=1920,
        help='Wallpaper width in pixels (default: 1920)'
    )
    parser.add_argument(
        '--height',
        type=int,
        default=1080,
        help='Wallpaper height in pixels (default: 1080)'
    )
    parser.add_argument(
        '--set-wallpaper',
        action='store_true',
        help='Automatically set the generated wallpaper'
    )
    parser.add_argument(
        '--life-output',
        type=str,
        default='life_calendar.png',
        help='Output filename for life calendar (default: life_calendar.png)'
    )
    parser.add_argument(
        '--year-output',
        type=str,
        default='year_calendar.png',
        help='Output filename for year calendar (default: year_calendar.png)'
    )
    parser.add_argument(
        '--title',
        type=str,
        default='',
        help='Custom title text to display on the wallpaper (single line)'
    )
    parser.add_argument(
        '--year-start',
        type=str,
        help='Start date for year calendar in YYYY-MM-DD format (default: Jan 1 of current year)'
    )
    parser.add_argument(
        '--year-end',
        type=str,
        help='End date for year calendar in YYYY-MM-DD format (default: Dec 31 of current year)'
    )
    
    args = parser.parse_args()
    
    # Validate birth date if needed
    birth_date = None
    if args.type in ['life', 'both']:
        if not args.birth_date:
            print("Error: --birth-date is required for life calendar")
            print("Usage: --birth-date YYYY-MM-DD")
            sys.exit(1)
        
        try:
            birth_date = datetime.strptime(args.birth_date, '%Y-%m-%d').date()
        except ValueError:
            print("Error: Invalid date format. Use YYYY-MM-DD (e.g., 1990-01-15)")
            sys.exit(1)
    
    # Parse year calendar dates if provided
    year_start_date = None
    year_end_date = None
    if args.type in ['year', 'both']:
        if args.year_start:
            try:
                year_start_date = datetime.strptime(args.year_start, '%Y-%m-%d').date()
            except ValueError:
                print("Error: Invalid year-start date format. Use YYYY-MM-DD (e.g., 2025-12-01)")
                sys.exit(1)
        
        if args.year_end:
            try:
                year_end_date = datetime.strptime(args.year_end, '%Y-%m-%d').date()
            except ValueError:
                print("Error: Invalid year-end date format. Use YYYY-MM-DD (e.g., 2026-05-01)")
                sys.exit(1)
        
        # Validate date range
        if year_start_date and year_end_date and year_start_date >= year_end_date:
            print("Error: Start date must be before end date")
            sys.exit(1)
    
    # Create output directory if it doesn't exist
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Initialize generator
    generator = LifeCalendarGenerator(width=args.width, height=args.height)
    
    # Generate wallpapers
    if args.type in ['life', 'both']:
        life_path = output_dir / args.life_output
        generator.generate_life_calendar(birth_date, str(life_path), custom_title=args.title or None)
        
        if args.set_wallpaper:
            set_wallpaper_linux_mint(str(life_path))
    
    if args.type in ['year', 'both']:
        year_path = output_dir / args.year_output
        generator.generate_year_calendar(str(year_path), year_start_date, year_end_date, custom_title=args.title or None)
        
        if args.set_wallpaper and args.type == 'year':
            set_wallpaper_linux_mint(str(year_path))


if __name__ == '__main__':
    main()
