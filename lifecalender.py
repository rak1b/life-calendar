#!/usr/bin/env python3
"""
Life Calendar Wallpaper Generator
Premium dark-themed wallpapers with unique colors every run.

Features:
- RANDOM COLOR THEMES: Fresh, unique palette on every generation
- DARK-BASED DESIGN: Deep backgrounds with muted, sophisticated dot colors
- AUTO-SCALING: Dot size and spacing adapt to any resolution (mobile → 4K)
- MONTH-ROW LAYOUT: Year calendar uses one row per month for clarity
- LIFE CALENDAR: Classic 52×90 week grid for lifetime visualization

Usage (crontab):
    python3 lifecalender.py --type year --year-start 2025-12-01 --year-end 2026-05-31 \
                            --title "180 DAYS" --set-wallpaper

    python3 lifecalender.py --type life --birth-date 1995-06-15 --set-wallpaper
"""

import os
import sys
import math
import random
import hashlib
import calendar
import colorsys
import argparse
import subprocess
from datetime import datetime, date, timedelta
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageFilter

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False


# =============================================================================
# COLOR THEME GENERATOR
# =============================================================================

class ColorTheme:
    """
    Generates rich, dark-based color themes with muted sophisticated palettes.

    By default, every call produces a UNIQUE theme (random seed).
    Pass seed='daily' to get one consistent theme per day (for crontab).

    Design philosophy:
    - Backgrounds are VERY dark (barely-there color tint)
    - Filled dots are muted mid-tones (visible but never flashy)
    - Empty dots are near-invisible ghost shapes
    - Today gets a moderate accent glow (not neon)
    """

    STRATEGIES = [
        'analogous',            # ±20–35° — smooth, calming
        'complementary',        # 180° apart — sophisticated contrast
        'triadic',              # 120° apart — balanced variety
        'split_complementary',  # 150°/210° — nuanced
        'monochrome',           # ±10° — elegant, unified
    ]

    def __init__(self, seed=None):
        """
        Args:
            seed: None=random each run, 'daily'=same per day, or any hashable value.
        """
        if seed == 'daily':
            day_str = date.today().isoformat()
            seed_int = int(hashlib.sha256(day_str.encode()).hexdigest(), 16)
            self.rng = random.Random(seed_int)
        elif seed is not None:
            self.rng = random.Random(seed)
        else:
            self.rng = random.Random()  # truly random each time
        self._generate()

    def _hsl(self, h, s, l):
        """HSL (h: 0-360, s: 0-1, l: 0-1) → RGB tuple (0-255)."""
        h_norm = (h % 360) / 360.0
        r, g, b = colorsys.hls_to_rgb(h_norm, l, s)
        return (int(r * 255), int(g * 255), int(b * 255))

    def _generate(self):
        rng = self.rng

        # ---- Base hue ----
        self.base_hue = rng.uniform(0, 360)
        h = self.base_hue

        # ---- Color harmony strategy ----
        self.strategy = rng.choice(self.STRATEGIES)

        # ---- Accent hues ----
        if self.strategy == 'analogous':
            off = rng.uniform(20, 35)
            accent_hues = [h, (h + off) % 360, (h - off) % 360]
        elif self.strategy == 'complementary':
            accent_hues = [h, (h + 180) % 360]
        elif self.strategy == 'triadic':
            accent_hues = [h, (h + 120) % 360, (h + 240) % 360]
        elif self.strategy == 'split_complementary':
            accent_hues = [h, (h + 150) % 360, (h + 210) % 360]
        else:  # monochrome
            accent_hues = [h, (h + 8) % 360, (h - 8) % 360]

        # ---- Background gradient corners (VERY dark, subtle tint) ----
        self.bg_corners = {
            'top_left':     self._hsl(h + rng.uniform(-5, 5),   rng.uniform(0.10, 0.22), rng.uniform(0.04, 0.065)),
            'top_right':    self._hsl(h + rng.uniform(5, 15),   rng.uniform(0.10, 0.22), rng.uniform(0.04, 0.065)),
            'bottom_left':  self._hsl(h + rng.uniform(-10, 0),  rng.uniform(0.08, 0.18), rng.uniform(0.025, 0.05)),
            'bottom_right': self._hsl(h + rng.uniform(0, 10),   rng.uniform(0.08, 0.18), rng.uniform(0.025, 0.05)),
        }

        # ---- Filled dot colors (muted mid-tones) ----
        self.filled_colors = []
        for ah in accent_hues[:4]:
            sat = rng.uniform(0.28, 0.48)
            lit = rng.uniform(0.38, 0.52)
            self.filled_colors.append(self._hsl(ah, sat, lit))
        while len(self.filled_colors) < 4:
            extra_h = (accent_hues[0] + rng.uniform(40, 60)) % 360
            self.filled_colors.append(self._hsl(extra_h, 0.35, 0.45))

        # ---- Empty dot colors (near-invisible ghosts) ----
        self.empty_colors = []
        for ah in accent_hues[:4]:
            sat = rng.uniform(0.04, 0.10)
            lit = rng.uniform(0.09, 0.14)
            self.empty_colors.append(self._hsl(ah, sat, lit))
        while len(self.empty_colors) < 4:
            self.empty_colors.append(self._hsl(h, 0.06, 0.11))

        # ---- Today dot: moderate accent (NOT neon) ----
        today_h = (h + rng.uniform(30, 70)) % 360
        self.today_dot  = self._hsl(today_h, 0.60, 0.58)
        self.today_ring = self._hsl(today_h, 0.40, 0.30)
        self.today_glow = self._hsl(today_h, 0.30, 0.18)

        # ---- Disabled dot (invisible placeholder) ----
        self.disabled_dot = self._hsl(h, 0.02, 0.055)

        # ---- Text colors (soft, never pure white) ----
        self.title_color     = (225, 225, 232)
        self.footer_color    = (155, 155, 168)
        self.label_color     = self._hsl(h, 0.12, 0.48)
        self.separator_color = self._hsl(h, 0.06, 0.16)

    def __repr__(self):
        return (f"ColorTheme(hue={self.base_hue:.0f}°, "
                f"strategy={self.strategy})")


# =============================================================================
# LIFE CALENDAR GENERATOR
# =============================================================================

class LifeCalendarGenerator:
    """
    Generates premium dark-themed Life Calendar and Year Calendar wallpapers.
    Auto-adapts to any screen size from mobile to 4K.
    """

    def __init__(self, width=1920, height=1080, seed=None):
        self.width = width
        self.height = height
        self.theme = ColorTheme(seed=seed)
        self._load_fonts()

    # ---- Font loading ----

    def _load_fonts(self):
        """Load fonts scaled to output dimensions."""
        scale = min(self.width, self.height) / 1080.0

        self.title_font_size  = max(13, int(30 * scale))
        self.footer_font_size = max(9,  int(16 * scale))
        self.label_font_size  = max(9,  int(15 * scale))

        font_paths = [
            "/usr/share/fonts/truetype/inter/Inter-SemiBold.ttf",
            "/usr/share/fonts/truetype/inter/Inter-Medium.ttf",
            "/usr/share/fonts/truetype/montserrat/Montserrat-SemiBold.ttf",
            "/usr/share/fonts/truetype/poppins/Poppins-Medium.ttf",
            "/usr/share/fonts/truetype/roboto/Roboto-Medium.ttf",
            "/usr/share/fonts/truetype/ubuntu/Ubuntu-Medium.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf",
        ]

        self.title_font = None
        self.footer_font = None
        self.label_font = None

        for path in font_paths:
            try:
                self.title_font  = ImageFont.truetype(path, self.title_font_size)
                self.footer_font = ImageFont.truetype(path, self.footer_font_size)
                self.label_font  = ImageFont.truetype(path, self.label_font_size)
                break
            except (OSError, IOError):
                continue

        if self.title_font is None:
            self.title_font  = ImageFont.load_default()
            self.footer_font = ImageFont.load_default()
            self.label_font  = ImageFont.load_default()

    # ---- Layout computation ----

    def _compute_layout(self, cols, rows, left_margin, right_margin,
                        top_margin, bottom_margin):
        """
        Compute optimal dot_size, spacing, and grid origin.
        Adapts dot-to-gap ratio for small vs large cells.
        """
        available_w = self.width  - left_margin - right_margin
        available_h = self.height - top_margin  - bottom_margin

        cell_w = available_w / max(1, cols)
        cell_h = available_h / max(1, rows)
        cell = min(cell_w, cell_h)

        # Tighter gaps at small sizes for better mobile density
        if cell <= 6:
            dot_fraction = 0.78
        elif cell <= 10:
            dot_fraction = 0.72
        elif cell <= 18:
            dot_fraction = 0.60
        else:
            dot_fraction = 0.50

        dot_size = max(3, int(cell * dot_fraction))
        spacing  = max(1, int(cell * (1.0 - dot_fraction)))

        # Generous caps for large screens
        dot_size = min(dot_size, 24)
        spacing  = min(spacing, 18)

        grid_width  = cols * (dot_size + spacing) - spacing
        grid_height = rows * (dot_size + spacing) - spacing

        start_x = left_margin + (available_w - grid_width)  // 2
        start_y = top_margin  + (available_h - grid_height) // 2

        return {
            'dot_size':    dot_size,
            'spacing':     spacing,
            'start_x':     start_x,
            'start_y':     start_y,
            'grid_width':  grid_width,
            'grid_height': grid_height,
        }

    # ---- Background rendering ----

    def _draw_gradient_background(self):
        """
        Rich dark gradient background with subtle vignette and organic noise.
        """
        corners = self.theme.bg_corners
        tl, tr = corners['top_left'], corners['top_right']
        bl, br = corners['bottom_left'], corners['bottom_right']

        if HAS_NUMPY:
            tl_a = np.array(tl, dtype=np.float32)
            tr_a = np.array(tr, dtype=np.float32)
            bl_a = np.array(bl, dtype=np.float32)
            br_a = np.array(br, dtype=np.float32)

            y_coords, x_coords = np.mgrid[0:self.height, 0:self.width].astype(np.float32)
            nx = x_coords / self.width
            ny = y_coords / self.height
            
            top    = tl_a[:, None, None] * (1 - nx) + tr_a[:, None, None] * nx
            bottom = bl_a[:, None, None] * (1 - nx) + br_a[:, None, None] * nx
            color  = top * (1 - ny) + bottom * ny

            # Subtle vignette (darken edges 10%)
            cx, cy = self.width / 2, self.height / 2
            max_dist = math.sqrt(cx ** 2 + cy ** 2)
            dist = np.sqrt((x_coords - cx) ** 2 + (y_coords - cy) ** 2)
            vignette = 1.0 - (dist / max_dist) * 0.10
            color = color * vignette
            
            # Gentle center brightening (8%)
            glow = 1.0 + (1.0 - dist / max_dist) * 0.08
            color = np.clip(color * glow, 0, 255)

            # Very subtle noise for organic texture
            noise = np.random.normal(1.0, 0.015, (3, self.height, self.width)).astype(np.float32)
            color = np.clip(color * noise, 0, 255)
            
            img_array = color.transpose(1, 2, 0).astype(np.uint8)
            return Image.fromarray(img_array, 'RGB')
        else:
            img = Image.new('RGB', (self.width, self.height), (8, 8, 12))
            draw = ImageDraw.Draw(img)
            chunk = max(1, self.height // 200)
            for y_start in range(0, self.height, chunk):
                y_end = min(y_start + chunk, self.height)
                ny = (y_start + y_end) / 2 / self.height
                for x in range(0, self.width, 5):
                    nx_val = x / self.width
                    r = int((tl[0]*(1-nx_val)+tr[0]*nx_val)*(1-ny) +
                            (bl[0]*(1-nx_val)+br[0]*nx_val)*ny)
                    g = int((tl[1]*(1-nx_val)+tr[1]*nx_val)*(1-ny) +
                            (bl[1]*(1-nx_val)+br[1]*nx_val)*ny)
                    b = int((tl[2]*(1-nx_val)+tr[2]*nx_val)*(1-ny) +
                            (bl[2]*(1-nx_val)+br[2]*nx_val)*ny)
                    draw.rectangle(
                        [(x, y_start), (min(x + 5, self.width), y_end)],
                        fill=(r, g, b)
                    )
            return img

    # ---- Date calculations ----

    def calculate_life_weeks(self, birth_date):
        today = date.today()
        expected_years = 90
        total_weeks = expected_years * 52
        total_days  = expected_years * 365
        days_lived = (today - birth_date).days
        weeks_lived = days_lived // 7
        return (weeks_lived, total_weeks, total_weeks - weeks_lived,
                days_lived, total_days, total_days - days_lived)

    def calculate_year_weeks(self, start_date=None, end_date=None):
        today = date.today()
        period_start = start_date if start_date else date(today.year, 1, 1)
        period_end   = end_date   if end_date   else date(today.year, 12, 31)
        total_days  = (period_end - period_start).days + 1
        total_weeks = (total_days + 6) // 7
        if today < period_start:
            days_elapsed = 0
        elif today > period_end:
            days_elapsed = total_days
        else:
            days_elapsed = (today - period_start).days + 1
        days_elapsed  = min(days_elapsed, total_days)
        weeks_elapsed = min(days_elapsed // 7, total_weeks)
        return (weeks_elapsed, total_weeks, total_weeks - weeks_elapsed,
                days_elapsed, total_days, total_days - days_elapsed)

    # ---- Generic dot grid (life calendar, etc.) ----

    def draw_grid(self, filled_count, total_count, title_text, footer_text,
                  grid_cols, grid_rows, current_day_index=None, dots_per_period=7):
        """
        Draw a clean dot grid. No flashy effects — just solid muted dots.
        """
        theme = self.theme
        img = self._draw_gradient_background()
        draw = ImageDraw.Draw(img)

        # Layout
        margin_x = max(15, int(self.width * 0.02))
        margin_top = max(50, int(self.height * 0.08))
        margin_bot = max(40, int(self.height * 0.06))
        layout = self._compute_layout(
            grid_cols, grid_rows,
            left_margin=margin_x, right_margin=margin_x,
            top_margin=margin_top, bottom_margin=margin_bot
        )
        dot_size = layout['dot_size']
        spacing  = layout['spacing']
        start_x  = layout['start_x']
        start_y  = layout['start_y']
        total_dots = min(total_count, grid_cols * grid_rows)

        # Title
        if title_text:
            bbox = draw.textbbox((0, 0), title_text, font=self.title_font)
            tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
            tx = start_x + (layout['grid_width'] - tw) // 2
            ty = max(8, start_y - th - max(14, int(22 * min(self.width, self.height) / 1080)))
            draw.text((tx + 1, ty + 1), title_text, fill=(0, 0, 0, 80), font=self.title_font)
            draw.text((tx, ty), title_text, fill=theme.title_color, font=self.title_font)

        # Draw dots — clean, minimal
        filled_colors = theme.filled_colors
        empty_colors  = theme.empty_colors
        dot_idx = 0

        for row in range(grid_rows):
            for col in range(grid_cols):
                if dot_idx >= total_dots:
                    break
                    
                x = start_x + col * (dot_size + spacing)
                y = start_y + row * (dot_size + spacing)

                period = dot_idx // dots_per_period
                color_idx = period % len(filled_colors)

                if dot_idx < filled_count:
                    if current_day_index is not None and dot_idx == current_day_index:
                        # Today: subtle glow
                        glow_r = max(2, dot_size // 3)
                        draw.ellipse(
                            [x - glow_r, y - glow_r,
                             x + dot_size + glow_r, y + dot_size + glow_r],
                            fill=theme.today_glow
                        )
                        dot_color = theme.today_dot
                    else:
                        dot_color = filled_colors[color_idx]
                else:
                    dot_color = empty_colors[color_idx]

                draw.ellipse([x, y, x + dot_size, y + dot_size], fill=dot_color)
                dot_idx += 1

            if dot_idx >= total_dots:
                break

        # Footer
        if footer_text:
            bbox = draw.textbbox((0, 0), footer_text, font=self.footer_font)
            fw = bbox[2] - bbox[0]
            fx = start_x + (layout['grid_width'] - fw) // 2
            fy = start_y + layout['grid_height'] + max(12, int(20 * min(self.width, self.height) / 1080))
            draw.text((fx + 1, fy + 1), footer_text, fill=(0, 0, 0, 80), font=self.footer_font)
            draw.text((fx, fy), footer_text, fill=theme.footer_color, font=self.footer_font)
        
        return img

    # ---- Month-row year calendar ----

    def draw_month_rows_year_calendar(self, period_start, period_end,
                                      title_text, footer_text):
        """
        Year calendar — one row per month, columns = days 1–31.
        Clean, minimal dot rendering with no flashy effects.
        """
        theme = self.theme
        img = self._draw_gradient_background()
        draw = ImageDraw.Draw(img)

        # Build month list
        months = []
        y, m = period_start.year, period_start.month
        while (y, m) <= (period_end.year, period_end.month):
            months.append((y, m))
            if m == 12:
                y += 1; m = 1
            else:
                m += 1

        num_months = max(1, len(months))
        cols = 31

        # Adaptive margins (tighter on mobile)
        scale = min(self.width, self.height) / 1080.0
        is_mobile = self.width < 500

        if is_mobile:
            label_w_estimate = max(24, int(5 * self.label_font_size))
            label_pad = max(2, int(4 * scale))
            left_margin  = label_w_estimate + label_pad + max(3, int(5 * scale))
            right_margin = max(3, int(5 * scale))
            top_margin   = max(35, int(50 * scale))
            bottom_margin = max(30, int(40 * scale))
        else:
            label_w_estimate = max(40, int(7 * self.label_font_size))
            label_pad = max(6, int(12 * scale))
            left_margin  = label_w_estimate + label_pad + max(10, int(16 * scale))
            right_margin = max(10, int(16 * scale))
            top_margin   = max(50, int(85 * scale))
            bottom_margin = max(40, int(65 * scale))

        layout = self._compute_layout(
            cols, num_months,
            left_margin=left_margin, right_margin=right_margin,
            top_margin=top_margin, bottom_margin=bottom_margin
        )
        dot_size = layout['dot_size']
        spacing  = layout['spacing']
        start_x  = layout['start_x']
        start_y  = layout['start_y']
        grid_w   = layout['grid_width']
        grid_h   = layout['grid_height']

        # Title
        if title_text:
            bbox = draw.textbbox((0, 0), title_text, font=self.title_font)
            tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
            tx = start_x + (grid_w - tw) // 2
            ty = max(8, start_y - th - max(10, int(18 * scale)))
            draw.text((tx + 1, ty + 1), title_text, fill=(0, 0, 0, 80), font=self.title_font)
            draw.text((tx, ty), title_text, fill=theme.title_color, font=self.title_font)

        # Subtle weekly separator lines (at day 7, 14, 21, 28)
        sep_w = 1
        for week_boundary in (7, 14, 21, 28):
            if week_boundary >= cols:
                continue
            sx = start_x + week_boundary * (dot_size + spacing) - spacing // 2
            draw.line(
                [(sx, start_y - 2), (sx, start_y + grid_h + 2)],
                fill=theme.separator_color, width=sep_w
            )

        # Dates
        today = date.today()
        if today < period_start:
            filled_until = period_start - timedelta(days=1)
        elif today > period_end:
            filled_until = period_end
        else:
            filled_until = today

        filled_colors = theme.filled_colors
        empty_colors  = theme.empty_colors

        for row_idx, (yr, mo) in enumerate(months):
            days_in_month = calendar.monthrange(yr, mo)[1]

            # Month label
            month_name = date(yr, mo, 1).strftime("%b %Y")
            lbbox = draw.textbbox((0, 0), month_name, font=self.label_font)
            lw = lbbox[2] - lbbox[0]
            lx = max(2, start_x - lw - label_pad)
            ly = start_y + row_idx * (dot_size + spacing) + (dot_size - (lbbox[3] - lbbox[1])) // 2
            draw.text((lx, ly), month_name, fill=theme.label_color, font=self.label_font)

            for col_idx in range(cols):
                x = start_x + col_idx * (dot_size + spacing)
                y_px = start_y + row_idx * (dot_size + spacing)

                day_num = col_idx + 1
                cell_date = date(yr, mo, day_num) if day_num <= days_in_month else None

                wg = (col_idx // 7) % len(filled_colors)

                # Disabled: out of month or out of range
                if cell_date is None or cell_date < period_start or cell_date > period_end:
                    draw.ellipse(
                        [x, y_px, x + dot_size, y_px + dot_size],
                        fill=theme.disabled_dot
                    )
                    continue

                is_filled = cell_date <= filled_until
                is_today = (cell_date == today and period_start <= today <= period_end)

                if is_today:
                    # Today: subtle glow
                    glow_r = max(2, dot_size // 3)
                    draw.ellipse(
                        [x - glow_r, y_px - glow_r,
                         x + dot_size + glow_r, y_px + dot_size + glow_r],
                        fill=theme.today_glow
                    )
                    dot_color = theme.today_dot
                elif is_filled:
                    dot_color = filled_colors[wg]
                else:
                    dot_color = empty_colors[wg]

                    draw.ellipse(
                    [x, y_px, x + dot_size, y_px + dot_size],
                    fill=dot_color
                )

        # Footer
        if footer_text:
            bbox = draw.textbbox((0, 0), footer_text, font=self.footer_font)
            fw = bbox[2] - bbox[0]
            fx = start_x + (grid_w - fw) // 2
            fy = start_y + grid_h + max(10, int(18 * scale))
            draw.text((fx + 1, fy + 1), footer_text, fill=(0, 0, 0, 80), font=self.footer_font)
            draw.text((fx, fy), footer_text, fill=theme.footer_color, font=self.footer_font)

        return img
    
    # ---- High-level generators ----
    
    def generate_life_calendar(self, birth_date, output_path, custom_title=None):
        (weeks_lived, total_weeks, weeks_remaining,
         days_lived, total_days, days_remaining) = self.calculate_life_weeks(birth_date)

        title = custom_title or "Life Calendar"
        pct = weeks_lived * 100 // total_weeks if total_weeks > 0 else 0
        footer = f"{weeks_remaining:,}w left · {pct}%"
        
        img = self.draw_grid(
            filled_count=weeks_lived,
            total_count=total_weeks,
            title_text=title,
            footer_text=footer,
            grid_cols=52,
            grid_rows=90,
            current_day_index=None,
            dots_per_period=4,
        )
        img.save(output_path, 'PNG', quality=95)
        print(f"Life Calendar saved: {output_path}")
        print(f"  Weeks: {weeks_lived:,} / {total_weeks:,} ({pct}%)")
        print(f"  Days:  {days_lived:,} / {total_days:,}")
        print(f"  Theme: {self.theme}")

    def generate_year_calendar(self, output_path, start_date=None,
                               end_date=None, custom_title=None):
        (weeks_elapsed, total_weeks, weeks_remaining,
         days_elapsed, total_days, days_remaining) = self.calculate_year_weeks(
            start_date, end_date
        )

        today = date.today()
        period_start = start_date if start_date else date(today.year, 1, 1)
        period_end   = end_date   if end_date   else date(today.year, 12, 31)

        if start_date and end_date:
            default_title = (f"{start_date.strftime('%b %d, %Y')} → "
                             f"{end_date.strftime('%b %d, %Y')}")
        else:
            default_title = "Year Calendar"
        
        title = custom_title or default_title
        pct = days_elapsed * 100 // total_days if total_days > 0 else 0
        footer = f"{days_remaining}d left · {pct}%"

        img = self.draw_month_rows_year_calendar(
            period_start=period_start,
            period_end=period_end,
            title_text=title,
            footer_text=footer,
        )
        img.save(output_path, 'PNG', quality=95)
        print(f"Year Calendar saved: {output_path}")
        print(f"  Days:  {days_elapsed} / {total_days} ({pct}%)")
        print(f"  Weeks: {weeks_elapsed} / {total_weeks}")
        print(f"  Theme: {self.theme}")


# =============================================================================
# WALLPAPER SETTER
# =============================================================================

def set_wallpaper_linux_mint(image_path):
    abs_path = os.path.abspath(image_path)
    if not os.path.exists(abs_path):
        print(f"Error: Image not found: {abs_path}")
        return False
    
    desktop = os.environ.get('XDG_CURRENT_DESKTOP', '').lower()
    
    try:
        if 'cinnamon' in desktop:
            subprocess.run([
                'gsettings', 'set', 'org.cinnamon.desktop.background',
                'picture-uri', f"file://{abs_path}"
            ], check=True)
            subprocess.run([
                'gsettings', 'set', 'org.cinnamon.desktop.background',
                'picture-options', 'scaled'
            ], check=True)
        elif 'mate' in desktop:
            subprocess.run([
                'gsettings', 'set', 'org.mate.background',
                'picture-filename', abs_path
            ], check=True)
        elif 'xfce' in desktop:
            subprocess.run([
                'xfconf-query', '-c', 'xfce4-desktop',
                '-p', '/backdrop/screen0/monitor0/workspace0/last-image',
                '-s', abs_path
            ], check=True)
        else:
            subprocess.run([
                'gsettings', 'set', 'org.gnome.desktop.background',
                'picture-uri', f"file://{abs_path}"
            ], check=True)
            
        print(f"Wallpaper set: {abs_path}")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print(f"Error setting wallpaper: {e}")
        return False


# =============================================================================
# CLI
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description='Generate premium dark Life Calendar / Year Calendar wallpapers'
    )
    parser.add_argument('--type', choices=['life', 'year', 'both'], default='both')
    parser.add_argument('--birth-date', type=str, help='YYYY-MM-DD (required for life)')
    parser.add_argument('--output-dir', type=str, default='.')
    parser.add_argument('--width',  type=int, default=1920)
    parser.add_argument('--height', type=int, default=1080)
    parser.add_argument('--set-wallpaper', action='store_true')
    parser.add_argument('--life-output', type=str, default='life_calendar.png')
    parser.add_argument('--year-output', type=str, default='year_calendar.png')
    parser.add_argument('--title', type=str, default='')
    parser.add_argument('--year-start', type=str)
    parser.add_argument('--year-end', type=str)
    parser.add_argument('--daily-seed', action='store_true',
                        help='Use date-based seed (same theme per day, for crontab)')
    
    args = parser.parse_args()
    
    # Validate birth date
    birth_date = None
    if args.type in ('life', 'both'):
        if not args.birth_date:
            print("Error: --birth-date required for life calendar")
            sys.exit(1)
        try:
            birth_date = datetime.strptime(args.birth_date, '%Y-%m-%d').date()
        except ValueError:
            print("Error: Invalid birth date. Use YYYY-MM-DD")
            sys.exit(1)
    
    # Validate year dates
    year_start = year_end = None
    if args.type in ('year', 'both'):
        if args.year_start:
            try:
                year_start = datetime.strptime(args.year_start, '%Y-%m-%d').date()
            except ValueError:
                print("Error: Invalid --year-start. Use YYYY-MM-DD")
                sys.exit(1)
        if args.year_end:
            try:
                year_end = datetime.strptime(args.year_end, '%Y-%m-%d').date()
            except ValueError:
                print("Error: Invalid --year-end. Use YYYY-MM-DD")
                sys.exit(1)
        if year_start and year_end and year_start >= year_end:
            print("Error: Start date must be before end date")
            sys.exit(1)
    
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    seed = 'daily' if args.daily_seed else None
    generator = LifeCalendarGenerator(
        width=args.width, height=args.height, seed=seed
    )
    custom_title = args.title or None

    if args.type in ('life', 'both'):
        path = output_dir / args.life_output
        generator.generate_life_calendar(birth_date, str(path), custom_title)
        if args.set_wallpaper:
            set_wallpaper_linux_mint(str(path))

    if args.type in ('year', 'both'):
        path = output_dir / args.year_output
        generator.generate_year_calendar(str(path), year_start, year_end, custom_title)
        if args.set_wallpaper and args.type == 'year':
            set_wallpaper_linux_mint(str(path))


if __name__ == '__main__':
    main()
