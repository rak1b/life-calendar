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
                  current_day_index=None, footer_text=None, dots_per_period=7):
        """
        Draw the calendar grid with dots.
        
        Args:
            filled_count: Number of filled dots
            total_count: Total number of dots to show
            title_text: Title to display (single line)
            subtitle_text: (Unused in current minimal UI, kept for backward compatibility)
            footer_text: Optional text to show below the grid (e.g., \"64d left · 28%\")
            dots_per_period: Number of dots per period (7 for weeks, 30 for months, etc.)
            
        Returns:
            PIL Image object
        """
        # Create image with modern dark background (slight gradient effect)
        img = Image.new('RGB', (self.width, self.height), self.bg_color)
        draw = ImageDraw.Draw(img)
        
        # Add subtle gradient background for modern look (optimized)
        # Top is slightly lighter, bottom is darker
        top_color = (15, 15, 22)
        bottom_color = (8, 8, 12)
        # Draw gradient in chunks for better performance
        chunk_size = max(1, self.height // 200)  # ~200 lines for smooth gradient
        for chunk_start in range(0, self.height, chunk_size):
            chunk_end = min(chunk_start + chunk_size, self.height)
            y_center = (chunk_start + chunk_end) // 2
            ratio = y_center / self.height
            r = int(top_color[0] * (1 - ratio) + bottom_color[0] * ratio)
            g = int(top_color[1] * (1 - ratio) + bottom_color[1] * ratio)
            b = int(top_color[2] * (1 - ratio) + bottom_color[2] * ratio)
            draw.rectangle([(0, chunk_start), (self.width, chunk_end)], fill=(r, g, b))
        
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
                    # Modern larger fonts with better readability
                    title_font = ImageFont.truetype(font_path, 32)
                    footer_font = ImageFont.truetype(font_path, 18)  # Larger footer
                    break
                except:
                    continue
        except:
            pass
        
        # Fallback to default if no font found
        if title_font is None:
            try:
                title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 36)
                footer_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 22)
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
            # Position title with more breathing room for modern look
            title_y = max(40, card_top - title_height - 50)
            
            # Modern title color: bright white with better contrast
            title_color = (255, 255, 255)
            # Draw subtle shadow/glow effect for depth
            shadow_offset = 2
            draw.text((title_x + shadow_offset, title_y + shadow_offset), title_text, 
                     fill=(0, 0, 0), font=title_font)
            draw.text((title_x, title_y), title_text, fill=title_color, font=title_font)
        
        # Modern dot palette with vibrant colors and better contrast
        # Base colors for filled and empty dots
        filled_dot_base = (255, 255, 255)     # pure white for filled dots
        empty_dot_base = (35, 35, 40)         # darker gray for empty dots
        today_dot = (100, 200, 255)          # bright cyan/blue highlight (modern accent)
        today_ring = (50, 150, 220)          # brighter ring for today's dot
        today_glow = (30, 100, 150)          # outer glow color
        
        # Color variations for weeks/months (very distinct colors for easy tracking)
        # Each period (week/month) gets a clearly different color to distinguish groups
        period_colors_filled = [
            (255, 255, 255),      # Pure white - Period 1 (Week 1, Month 1, etc.)
            (180, 210, 255),      # Light blue - Period 2 (very visible blue tint)
            (255, 210, 180),      # Light coral - Period 3 (very visible orange tint)
            (180, 255, 210),      # Light green - Period 4 (very visible green tint)
        ]
        period_colors_empty = [
            (35, 35, 40),         # Dark gray - Period 1
            (35, 38, 50),         # Dark blue-gray - Period 2 (more distinct)
            (50, 38, 35),         # Dark orange-gray - Period 3 (more distinct)
            (38, 50, 40),         # Dark green-gray - Period 4 (more distinct)
        ]
        
        # Track previous period to draw separators
        prev_period_index = -1

        # Draw dots
        dot_index = 0
        for row in range(rows):
            for col in range(cols):
                if dot_index >= total_dots_to_show:
                    break
                    
                x = start_x + col * (self.dot_size + self.spacing)
                y = start_y + row * (self.dot_size + self.spacing)
                
                # Determine which period (week/month) this dot belongs to
                period_index = dot_index // dots_per_period
                period_color_index = period_index % len(period_colors_filled)
                
                # Draw subtle separator line between periods (weeks/months)
                # Draw a thin vertical line before the first dot of each new period
                if period_index != prev_period_index and prev_period_index != -1 and col > 0:
                    # Draw a subtle separator line between periods
                    separator_x = x - self.spacing // 2
                    separator_color = (70, 70, 75)  # Subtle gray separator
                    # Draw vertical line spanning the dot height
                    draw.line(
                        [(separator_x, y - self.dot_size // 2), 
                         (separator_x, y + self.dot_size + self.spacing // 2)],
                        fill=separator_color,
                        width=2
                    )
                prev_period_index = period_index
                
                # Determine if this dot should be filled
                if dot_index < filled_count:
                    # Highlight current day with modern glow effect
                    if current_day_index is not None and dot_index == current_day_index:
                        # Draw outer glow (largest circle)
                        glow_pad = 6
                        draw.ellipse(
                            [x - glow_pad, y - glow_pad, 
                             x + self.dot_size + glow_pad, y + self.dot_size + glow_pad],
                            fill=today_glow,
                            outline=None
                        )
                        # Draw middle ring
                        ring_pad = 3
                        draw.ellipse(
                            [x - ring_pad, y - ring_pad, 
                             x + self.dot_size + ring_pad, y + self.dot_size + ring_pad],
                            fill=today_ring,
                            outline=None
                        )
                        dot_color = today_dot
                    else:
                        # Use period-specific color for filled dots
                        filled_dot = period_colors_filled[period_color_index]
                        # Add subtle glow to filled dots for modern look
                        glow_pad = 2
                        # Darker glow that matches the period color (more visible)
                        glow_color_r = max(40, filled_dot[0] - 30)
                        glow_color_g = max(40, filled_dot[1] - 30)
                        glow_color_b = max(40, filled_dot[2] - 30)
                        draw.ellipse(
                            [x - glow_pad, y - glow_pad, 
                             x + self.dot_size + glow_pad, y + self.dot_size + glow_pad],
                            fill=(glow_color_r, glow_color_g, glow_color_b),
                            outline=None
                        )
                        dot_color = filled_dot
                else:
                    # Use period-specific color for empty dots
                    dot_color = period_colors_empty[period_color_index]
                
                # Draw dot as a circle with modern styling
                draw.ellipse(
                    [x, y, x + self.dot_size, y + self.dot_size],
                    fill=dot_color,
                    outline=None
                )
                
                # Add subtle highlight to filled dots for depth (modern 3D effect)
                if dot_index < filled_count and (current_day_index is None or dot_index != current_day_index):
                    highlight_size = self.dot_size // 3
                    highlight_x = x + self.dot_size // 3
                    highlight_y = y + self.dot_size // 3
                    # Use lighter white for highlight effect
                    draw.ellipse(
                        [highlight_x, highlight_y, 
                         highlight_x + highlight_size, highlight_y + highlight_size],
                        fill=(255, 255, 255),
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
            # More spacing for modern look
            footer_y = card_bottom + 40

            # Modern footer color: bright white with better contrast
            footer_color = (220, 220, 225)
            # Add subtle shadow for depth
            shadow_offset = 1
            draw.text((footer_x + shadow_offset, footer_y + shadow_offset), footer_text, 
                     fill=(0, 0, 0), font=footer_font)
            draw.text((footer_x, footer_y), footer_text, fill=footer_color, font=footer_font)
        
        return img

    def draw_month_rows_year_calendar(self, period_start, period_end, title_text, footer_text):
        """
        Draw a Year Calendar where **each row is a month** and each column is a day (1..31).

        This makes it much easier to track month progress at a glance compared to a continuous
        day stream.

        Rendering rules:
        - Rows: one per month between period_start and period_end (inclusive).
        - Columns: 31 (days). Days that don't exist in that month are shown as faint placeholders.
        - Days outside the selected period range are also shown as faint placeholders.
        - Filled vs empty is based on today's date (date.today()) intersected with the period.
        - Week color grouping is done within each month row: every 7 columns is a "week group".
        """
        # --- Background + fonts (kept consistent with draw_grid) ---
        img = Image.new('RGB', (self.width, self.height), self.bg_color)
        draw = ImageDraw.Draw(img)

        # Subtle dark gradient background (optimized)
        top_color = (15, 15, 22)
        bottom_color = (8, 8, 12)
        chunk_size = max(1, self.height // 200)
        for chunk_start in range(0, self.height, chunk_size):
            chunk_end = min(chunk_start + chunk_size, self.height)
            y_center = (chunk_start + chunk_end) // 2
            ratio = y_center / self.height
            r = int(top_color[0] * (1 - ratio) + bottom_color[0] * ratio)
            g = int(top_color[1] * (1 - ratio) + bottom_color[1] * ratio)
            b = int(top_color[2] * (1 - ratio) + bottom_color[2] * ratio)
            draw.rectangle([(0, chunk_start), (self.width, chunk_end)], fill=(r, g, b))

        # Try to load a modern font, fallback to DejaVu
        title_font = None
        footer_font = None
        label_font = None
        font_paths = [
            "/usr/share/fonts/truetype/montserrat/Montserrat-Bold.ttf",
            "/usr/share/fonts/truetype/poppins/Poppins-Bold.ttf",
            "/usr/share/fonts/truetype/raleway/Raleway-Bold.ttf",
            "/usr/share/fonts/truetype/inter/Inter-Bold.ttf",
            "/usr/share/fonts/truetype/roboto/Roboto-Bold.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        ]
        for font_path in font_paths:
            try:
                title_font = ImageFont.truetype(font_path, 32)
                footer_font = ImageFont.truetype(font_path, 18)
                label_font = ImageFont.truetype(font_path, 16)
                break
            except Exception:
                continue
        if title_font is None:
            title_font = ImageFont.load_default()
            footer_font = ImageFont.load_default()
            label_font = ImageFont.load_default()

        # --- Layout ---
        # Build the month list between start and end (inclusive)
        months = []
        year, month = period_start.year, period_start.month
        while (year, month) <= (period_end.year, period_end.month):
            months.append((year, month))
            if month == 12:
                year += 1
                month = 1
            else:
                month += 1

        cols = 31
        rows = max(1, len(months))
        total_dots_to_show = cols * rows

        grid_width = cols * (self.dot_size + self.spacing) - self.spacing
        grid_height = rows * (self.dot_size + self.spacing) - self.spacing
        start_x = (self.width - grid_width) // 2
        start_y = (self.height - grid_height) // 2

        # Title (centered)
        if title_text:
            title_bbox = draw.textbbox((0, 0), title_text, font=title_font)
            title_width = title_bbox[2] - title_bbox[0]
            title_height = title_bbox[3] - title_bbox[1]
            title_x = start_x + (grid_width - title_width) // 2
            title_y = max(40, start_y - title_height - 50)
            draw.text((title_x + 2, title_y + 2), title_text, fill=(0, 0, 0), font=title_font)
            draw.text((title_x, title_y), title_text, fill=(255, 255, 255), font=title_font)

        # --- Colors ---
        # Distinct week-group colors (cycled within each month row)
        period_colors_filled = [
            (255, 255, 255),  # Week-group 1
            (180, 210, 255),  # Week-group 2 (blue)
            (255, 210, 180),  # Week-group 3 (coral)
            (180, 255, 210),  # Week-group 4 (green)
        ]
        period_colors_empty = [
            (35, 35, 40),
            (35, 38, 50),
            (50, 38, 35),
            (38, 50, 40),
        ]

        today_dot = (100, 200, 255)
        today_ring = (50, 150, 220)
        today_glow = (30, 100, 150)

        # Very faint placeholder for non-existing days and out-of-range days
        disabled_dot = (22, 22, 28)

        # --- Draw monthly rows ---
        today = date.today()
        # Clamp for fill logic (if the period is fully in the past/future)
        if today < period_start:
            filled_until = period_start - timedelta(days=1)  # nothing filled
        elif today > period_end:
            filled_until = period_end  # everything in range filled
        else:
            filled_until = today

        # Month labels on the left (small, subtle)
        label_color = (170, 170, 180)
        label_padding = 18

        # Draw weekly separators (vertical) for readability: after day 7, 14, 21, 28
        separator_color = (70, 70, 75)
        for week_boundary in (7, 14, 21, 28):
            sep_x = start_x + week_boundary * (self.dot_size + self.spacing) - (self.spacing // 2)
            draw.line([(sep_x, start_y - 6), (sep_x, start_y + grid_height + 6)], fill=separator_color, width=2)

        for row_idx, (y, m) in enumerate(months):
            days_in_month = calendar.monthrange(y, m)[1]

            # Label like "Dec 2025"
            month_name = date(y, m, 1).strftime("%b %Y")
            label_bbox = draw.textbbox((0, 0), month_name, font=label_font)
            label_width = label_bbox[2] - label_bbox[0]
            label_x = max(20, start_x - label_width - label_padding)
            label_y = start_y + row_idx * (self.dot_size + self.spacing) - 2
            draw.text((label_x, label_y), month_name, fill=label_color, font=label_font)

            for col_idx in range(cols):
                x = start_x + col_idx * (self.dot_size + self.spacing)
                y_px = start_y + row_idx * (self.dot_size + self.spacing)

                # Resolve the actual date for this cell (or None if day doesn't exist)
                day_num = col_idx + 1
                if day_num > days_in_month:
                    cell_date = None
                else:
                    cell_date = date(y, m, day_num)

                # Determine week-group color inside the month row
                week_group_index = (col_idx // 7) % len(period_colors_filled)

                # Disabled cells: outside month OR outside chosen range
                if cell_date is None or cell_date < period_start or cell_date > period_end:
                    draw.ellipse(
                        [x, y_px, x + self.dot_size, y_px + self.dot_size],
                        fill=disabled_dot,
                        outline=None
                    )
                    continue

                # Filled vs empty
                is_filled = cell_date <= filled_until
                dot_color = period_colors_filled[week_group_index] if is_filled else period_colors_empty[week_group_index]

                # Today highlight (only when today is inside the period)
                if cell_date == today and period_start <= today <= period_end:
                    glow_pad = 6
                    draw.ellipse(
                        [x - glow_pad, y_px - glow_pad,
                         x + self.dot_size + glow_pad, y_px + self.dot_size + glow_pad],
                        fill=today_glow,
                        outline=None
                    )
                    ring_pad = 3
                    draw.ellipse(
                        [x - ring_pad, y_px - ring_pad,
                         x + self.dot_size + ring_pad, y_px + self.dot_size + ring_pad],
                        fill=today_ring,
                        outline=None
                    )
                    dot_color = today_dot

                # Draw dot
                draw.ellipse([x, y_px, x + self.dot_size, y_px + self.dot_size], fill=dot_color, outline=None)

        # Footer (centered)
        if footer_text:
            footer_bbox = draw.textbbox((0, 0), footer_text, font=footer_font)
            footer_width = footer_bbox[2] - footer_bbox[0]
            footer_x = start_x + (grid_width - footer_width) // 2
            footer_y = start_y + grid_height + 40
            draw.text((footer_x + 1, footer_y + 1), footer_text, fill=(0, 0, 0), font=footer_font)
            draw.text((footer_x, footer_y), footer_text, fill=(220, 220, 225), font=footer_font)

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
        # Group by months (approximately 4 weeks per month) for color coding
        img = self.draw_grid(
            weeks_lived,
            total_weeks,
            title,
            subtitle,
            grid_cols=52,
            grid_rows=90,
            start_date=None,
            end_date=None,
            current_day_index=None,  # Life calendar uses weeks, not days
            dots_per_period=4  # 4 weeks per month for color grouping
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
        
        # Resolve the actual period range (must match calculate_year_weeks defaults)
        today = date.today()
        period_start = start_date if start_date is not None else date(today.year, 1, 1)
        period_end = end_date if end_date is not None else date(today.year, 12, 31)

        # Footer text: "Xd left · Y%"
        percent_done = days_elapsed * 100 // total_days if total_days > 0 else 0
        days_left = days_remaining
        footer_text = f"{days_left}d left · {percent_done}%"

        # Month-row layout: each row = one month, columns = days 1..31
        img = self.draw_month_rows_year_calendar(
            period_start=period_start,
            period_end=period_end,
            title_text=title,
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
