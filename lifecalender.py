#!/usr/bin/env python3
"""
Life Calendar Wallpaper Generator
Generates beautiful, dynamic wallpapers showing life progress in weeks or year progress.

Key features:
- DYNAMIC COLOR THEMES: Each day produces a unique color scheme using HSL color theory
  (complementary, triadic, analogous, split-complementary, tetradic harmonies).
- AUTO-SCALING: Dot size, spacing, and fonts adapt to any resolution (mobile → 4K).
- MONTH-ROW LAYOUT: Year calendar uses one row per month for easy tracking.
- LIFE CALENDAR: Classic 52×90 week grid for lifetime visualization.

Usage (crontab):
    python3 lifecalender.py --type year --year-start 2025-12-01 --year-end 2026-05-31 \\
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

from PIL import Image, ImageDraw, ImageFont

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False


# =============================================================================
# DYNAMIC THEME GENERATOR
# =============================================================================

class DailyTheme:
    """
    Generates a unique, harmonious color theme for each day using HSL color theory.

    The current date is used as a seed, so:
    - Same day always produces the same theme (safe for multiple crontab runs)
    - Each new day is a completely different look (365+ unique themes per year)
    - Colors are always harmonious thanks to color theory strategies
    """

    # Color harmony strategies for generating related hues
    STRATEGIES = [
        'complementary',       # 2 hues, 180° apart — bold contrast
        'analogous',           # 3 hues, ±30° apart — smooth, calming
        'triadic',             # 3 hues, 120° apart — vibrant, balanced
        'split_complementary', # 3 hues: base + 150° + 210° — nuanced contrast
        'tetradic',            # 4 hues, 90° apart — rich and complex
    ]

    def __init__(self, seed_date=None):
        """
        Args:
            seed_date: The date to seed the theme from. Defaults to today.
        """
        self.seed_date = seed_date or date.today()
        # SHA-256 hash of the date string → deterministic seed
        seed_int = int(hashlib.sha256(
            self.seed_date.isoformat().encode()
        ).hexdigest(), 16)
        self.rng = random.Random(seed_int)
        self._generate()

    # ---- internal helpers ----

    def _hsl_to_rgb(self, h, s, l):
        """Convert HSL (hue 0-360, saturation 0-1, lightness 0-1) → RGB (0-255)."""
        h_norm = (h % 360) / 360.0
        r, g, b = colorsys.hls_to_rgb(h_norm, l, s)  # note: Python uses HLS order
        return (int(r * 255), int(g * 255), int(b * 255))

    def _generate(self):
        """Build the complete daily theme: background, dots, today highlight, text."""
        rng = self.rng

        # ---- 1. Base hue: the "mood" of the day (0–360°) ----
        self.base_hue = rng.uniform(0, 360)
        h = self.base_hue

        # ---- 2. Choose a color harmony strategy ----
        self.strategy = rng.choice(self.STRATEGIES)

        # ---- 3. Derive accent hues from the strategy ----
        if self.strategy == 'complementary':
            accent_hues = [h, (h + 180) % 360]
        elif self.strategy == 'analogous':
            offset = rng.uniform(25, 40)
            accent_hues = [h, (h + offset) % 360, (h - offset) % 360]
        elif self.strategy == 'triadic':
            accent_hues = [h, (h + 120) % 360, (h + 240) % 360]
        elif self.strategy == 'split_complementary':
            accent_hues = [h, (h + 150) % 360, (h + 210) % 360]
        else:  # tetradic
            accent_hues = [h, (h + 90) % 360, (h + 180) % 360, (h + 270) % 360]

        # ---- 4. Background gradient corners (very dark, subtle tint) ----
        self.bg_corners = {}
        corner_specs = {
            'top_left':     (rng.uniform(-5, 5),    rng.uniform(0.30, 0.65), rng.uniform(0.07, 0.14)),
            'top_right':    (rng.uniform(10, 25),   rng.uniform(0.30, 0.65), rng.uniform(0.07, 0.14)),
            'bottom_left':  (rng.uniform(-15, -5),  rng.uniform(0.25, 0.55), rng.uniform(0.03, 0.09)),
            'bottom_right': (rng.uniform(5, 15),    rng.uniform(0.25, 0.55), rng.uniform(0.03, 0.09)),
        }
        for name, (hue_offset, sat, light) in corner_specs.items():
            self.bg_corners[name] = self._hsl_to_rgb(h + hue_offset, sat, light)

        # ---- 5. Filled dot colors (bright, high-saturation, different hues) ----
        self.filled_colors = []
        for accent_h in accent_hues[:4]:
            sat = rng.uniform(0.45, 0.75)
            light = rng.uniform(0.72, 0.88)
            self.filled_colors.append(self._hsl_to_rgb(accent_h, sat, light))
        # Pad to 4 colors if fewer than 4 accent hues
        while len(self.filled_colors) < 4:
            extra_hue = (accent_hues[0] + rng.uniform(50, 80)) % 360
            self.filled_colors.append(self._hsl_to_rgb(extra_hue, 0.55, 0.80))

        # ---- 6. Empty dot colors (same hues but very dark/muted) ----
        self.empty_colors = []
        for accent_h in accent_hues[:4]:
            sat = rng.uniform(0.15, 0.35)
            light = rng.uniform(0.10, 0.17)
            self.empty_colors.append(self._hsl_to_rgb(accent_h, sat, light))
        while len(self.empty_colors) < 4:
            extra_hue = (accent_hues[0] + rng.uniform(50, 80)) % 360
            self.empty_colors.append(self._hsl_to_rgb(extra_hue, 0.20, 0.14))

        # ---- 7. Today's dot: vibrant accent with glow layers ----
        today_hue = (h + rng.uniform(40, 80)) % 360
        self.today_dot  = self._hsl_to_rgb(today_hue, 0.85, 0.68)
        self.today_ring = self._hsl_to_rgb(today_hue, 0.75, 0.48)
        self.today_glow = self._hsl_to_rgb(today_hue, 0.65, 0.30)

        # ---- 8. Disabled dot (nearly invisible placeholder) ----
        self.disabled_dot = self._hsl_to_rgb(h, 0.08, 0.09)

        # ---- 9. UI text colors (white-ish with subtle hue tint) ----
        self.title_color     = (255, 255, 255)
        self.footer_color    = (220, 220, 225)
        self.label_color     = self._hsl_to_rgb(h, 0.15, 0.72)
        self.separator_color = self._hsl_to_rgb(h, 0.10, 0.28)

    def __repr__(self):
        return (f"DailyTheme(date={self.seed_date}, hue={self.base_hue:.0f}°, "
                f"strategy={self.strategy})")


# =============================================================================
# LIFE CALENDAR GENERATOR
# =============================================================================

class LifeCalendarGenerator:
    """
    Generates Life Calendar and Year Calendar wallpapers.

    Adapts dot size, spacing, and fonts automatically based on output dimensions
    so it works on any screen: mobile (390×844), desktop (1920×1080), 4K, etc.
    """

    def __init__(self, width=1920, height=1080):
        """
        Args:
            width:  Output image width in pixels.
            height: Output image height in pixels.
        """
        self.width = width
        self.height = height
        self.theme = DailyTheme()
        self._load_fonts()

    # ---- Font loading ----

    def _load_fonts(self):
        """Load fonts with sizes scaled to the output dimensions."""
        # Scale factor: 1.0 at 1080p's smaller dimension
        scale = min(self.width, self.height) / 1080.0

        self.title_font_size  = max(12, int(32 * scale))
        self.footer_font_size = max(9,  int(18 * scale))
        self.label_font_size  = max(8,  int(16 * scale))

        # Preferred modern fonts (ordered by preference)
        font_paths = [
            "/usr/share/fonts/truetype/montserrat/Montserrat-Bold.ttf",
            "/usr/share/fonts/truetype/poppins/Poppins-Bold.ttf",
            "/usr/share/fonts/truetype/raleway/Raleway-Bold.ttf",
            "/usr/share/fonts/truetype/inter/Inter-Bold.ttf",
            "/usr/share/fonts/truetype/roboto/Roboto-Bold.ttf",
            "/usr/share/fonts/truetype/ubuntu/Ubuntu-Bold.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf",
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

        # Ultimate fallback
        if self.title_font is None:
            self.title_font  = ImageFont.load_default()
            self.footer_font = ImageFont.load_default()
            self.label_font  = ImageFont.load_default()

    # ---- Layout computation ----

    def _compute_layout(self, cols, rows, left_margin, right_margin,
                        top_margin, bottom_margin):
        """
        Compute optimal dot_size, spacing, and grid origin for a given grid.

        The algorithm:
        1. Calculate the largest cell that fits both horizontally and vertically.
        2. Split the cell into dot (larger portion) and spacing (smaller portion),
           using adaptive ratios so tiny dots get tighter gaps.
        3. Center the resulting grid within the available area.

        Returns:
            dict with keys: dot_size, spacing, start_x, start_y,
                            grid_width, grid_height
        """
        available_w = self.width  - left_margin - right_margin
        available_h = self.height - top_margin  - bottom_margin

        # Maximum cell size that fits in both dimensions
        cell_w = available_w / max(1, cols)
        cell_h = available_h / max(1, rows)
        cell = min(cell_w, cell_h)

        # Adaptive dot-to-spacing ratio: tighter gaps at small sizes
        if cell <= 8:
            dot_fraction = 0.65
        elif cell <= 15:
            dot_fraction = 0.55
        else:
            dot_fraction = 0.42  # More breathing room at larger sizes

        dot_size = max(3, int(cell * dot_fraction))
        spacing  = max(1, int(cell * (1.0 - dot_fraction)))

        # Reasonable caps so desktop/4K doesn't produce absurdly large dots
        dot_size = min(dot_size, 18)
        spacing  = min(spacing, 24)

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
        Create a beautiful gradient background using the daily theme's corner colors.

        Uses bilinear interpolation across 4 corners with:
        - Radial vignette (darker edges)
        - Center glow (brighter center)
        - Subtle noise texture (organic feel)

        Returns a PIL Image.
        """
        corners = self.theme.bg_corners
        tl, tr = corners['top_left'], corners['top_right']
        bl, br = corners['bottom_left'], corners['bottom_right']

        if HAS_NUMPY:
            tl_a = np.array(tl, dtype=np.float32)
            tr_a = np.array(tr, dtype=np.float32)
            bl_a = np.array(bl, dtype=np.float32)
            br_a = np.array(br, dtype=np.float32)

            # Coordinate grids (vectorized for speed)
            y_coords, x_coords = np.mgrid[0:self.height, 0:self.width].astype(np.float32)
            nx = x_coords / self.width
            ny = y_coords / self.height

            # Bilinear interpolation of the four corners
            top    = tl_a[:, None, None] * (1 - nx) + tr_a[:, None, None] * nx
            bottom = bl_a[:, None, None] * (1 - nx) + br_a[:, None, None] * nx
            color  = top * (1 - ny) + bottom * ny

            # Radial vignette (darken edges 15%)
            cx, cy = self.width / 2, self.height / 2
            max_dist = math.sqrt(cx ** 2 + cy ** 2)
            dist = np.sqrt((x_coords - cx) ** 2 + (y_coords - cy) ** 2)
            vignette = 1.0 - (dist / max_dist) * 0.15
            color = color * vignette

            # Center glow (brighten center 20%)
            glow = 1.0 + (1.0 - dist / max_dist) * 0.20
            color = np.clip(color * glow, 0, 255)

            # Subtle noise texture
            noise = np.random.normal(1.0, 0.025, (3, self.height, self.width)).astype(np.float32)
            color = np.clip(color * noise, 0, 255)

            img_array = color.transpose(1, 2, 0).astype(np.uint8)
            return Image.fromarray(img_array, 'RGB')

        else:
            # Fallback: chunked bilinear interpolation (no numpy)
            img = Image.new('RGB', (self.width, self.height), (10, 10, 15))
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
        """
        Calculate weeks lived and remaining in expected 90-year lifespan.

        Returns:
            (weeks_lived, total_weeks, weeks_remaining,
             days_lived, total_days, days_remaining)
        """
        today = date.today()
        expected_years = 90
        total_weeks = expected_years * 52
        total_days  = expected_years * 365

        days_lived = (today - birth_date).days
        weeks_lived = days_lived // 7

        return (weeks_lived, total_weeks, total_weeks - weeks_lived,
                days_lived, total_days, total_days - days_lived)

    def calculate_year_weeks(self, start_date=None, end_date=None):
        """
        Calculate days/weeks elapsed in a custom period.

        Returns:
            (weeks_elapsed, total_weeks, weeks_remaining,
             days_elapsed, total_days, days_remaining)
        """
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

    # ---- Grid drawing (for life calendar and generic day grids) ----

    def draw_grid(self, filled_count, total_count, title_text, footer_text,
                  grid_cols, grid_rows, current_day_index=None, dots_per_period=7):
        """
        Draw a generic calendar dot grid.

        Used for life calendars (52×90 weeks) and simple day grids.
        Each dot is colored using the daily theme's filled/empty colors, with
        period-based color cycling (e.g., every 7 dots = one week gets same color).

        Args:
            filled_count:     Number of filled (completed) dots.
            total_count:      Total dots to render.
            title_text:       Title string above the grid.
            footer_text:      Footer string below the grid.
            grid_cols:        Number of columns in the grid.
            grid_rows:        Number of rows in the grid.
            current_day_index: 0-based index of today's dot (or None).
            dots_per_period:  Dots per color-group (7=week, 4=month, etc.).

        Returns:
            PIL Image object.
        """
        theme = self.theme

        # ---- Background ----
        img = self._draw_gradient_background()
        draw = ImageDraw.Draw(img)

        # ---- Layout (auto-scaled) ----
        margin_x = max(20, int(self.width * 0.02))
        margin_top = max(60, int(self.height * 0.09))
        margin_bot = max(50, int(self.height * 0.07))
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

        # ---- Title ----
        if title_text:
            bbox = draw.textbbox((0, 0), title_text, font=self.title_font)
            tw = bbox[2] - bbox[0]
            th = bbox[3] - bbox[1]
            tx = start_x + (layout['grid_width'] - tw) // 2
            ty = max(10, start_y - th - max(20, int(30 * min(self.width, self.height) / 1080)))
            # Shadow for depth
            draw.text((tx + 2, ty + 2), title_text, fill=(0, 0, 0), font=self.title_font)
            draw.text((tx, ty), title_text, fill=theme.title_color, font=self.title_font)

        # ---- Draw dots ----
        filled_colors = theme.filled_colors
        empty_colors  = theme.empty_colors
        sep_color     = theme.separator_color
        prev_period   = -1
        dot_idx       = 0
        sep_width     = 1 if dot_size < 6 else 2

        for row in range(grid_rows):
            for col in range(grid_cols):
                if dot_idx >= total_dots:
                    break

                x = start_x + col * (dot_size + spacing)
                y = start_y + row * (dot_size + spacing)

                # Period grouping (e.g., every 7 dots = one week)
                period = dot_idx // dots_per_period
                color_idx = period % len(filled_colors)

                # Separator line between period groups
                if period != prev_period and prev_period != -1 and col > 0:
                    sx = x - spacing // 2
                    draw.line(
                        [(sx, y - dot_size // 4), (sx, y + dot_size + spacing // 4)],
                        fill=sep_color, width=sep_width
                    )
                prev_period = period

                # ---- Dot rendering ----
                if dot_idx < filled_count:
                    if current_day_index is not None and dot_idx == current_day_index:
                        # Today's dot: three-layer glow
                        glow_pad = max(3, dot_size // 2)
                        ring_pad = max(2, dot_size // 4)
                        draw.ellipse(
                            [x - glow_pad, y - glow_pad,
                             x + dot_size + glow_pad, y + dot_size + glow_pad],
                            fill=theme.today_glow
                        )
                        draw.ellipse(
                            [x - ring_pad, y - ring_pad,
                             x + dot_size + ring_pad, y + dot_size + ring_pad],
                            fill=theme.today_ring
                        )
                        dot_color = theme.today_dot
                    else:
                        # Filled dot with subtle glow
                        fc = filled_colors[color_idx]
                        glow_pad = max(1, dot_size // 7)
                        glow_color = tuple(max(30, c - 40) for c in fc)
                        draw.ellipse(
                            [x - glow_pad, y - glow_pad,
                             x + dot_size + glow_pad, y + dot_size + glow_pad],
                            fill=glow_color
                        )
                        dot_color = fc
                else:
                    # Empty (future) dot
                    dot_color = empty_colors[color_idx]

                # The dot itself
                draw.ellipse(
                    [x, y, x + dot_size, y + dot_size],
                    fill=dot_color
                )

                # Highlight on filled dots for subtle 3D depth
                if dot_idx < filled_count and not (
                    current_day_index is not None and dot_idx == current_day_index
                ):
                    hs = max(1, dot_size // 4)
                    hx = x + dot_size // 3
                    hy = y + dot_size // 4
                    draw.ellipse([hx, hy, hx + hs, hy + hs], fill=(255, 255, 255))

                dot_idx += 1

            if dot_idx >= total_dots:
                break

        # ---- Footer ----
        if footer_text:
            bbox = draw.textbbox((0, 0), footer_text, font=self.footer_font)
            fw = bbox[2] - bbox[0]
            fx = start_x + (layout['grid_width'] - fw) // 2
            fy = start_y + layout['grid_height'] + max(15, int(25 * min(self.width, self.height) / 1080))
            draw.text((fx + 1, fy + 1), footer_text, fill=(0, 0, 0), font=self.footer_font)
            draw.text((fx, fy), footer_text, fill=theme.footer_color, font=self.footer_font)

        return img

    # ---- Month-row calendar drawing ----

    def draw_month_rows_year_calendar(self, period_start, period_end,
                                      title_text, footer_text):
        """
        Draw a Year Calendar where each row is one month, columns are days 1–31.

        Features:
        - Month labels on the left (e.g., "Dec 2025")
        - Weekly color grouping within each row (every 7 days)
        - Vertical separator lines at week boundaries (day 7, 14, 21, 28)
        - Today highlighted with a glowing accent dot
        - Disabled (grayed out) dots for non-existent days and out-of-range days

        Returns:
            PIL Image object.
        """
        theme = self.theme

        # ---- Background ----
        img = self._draw_gradient_background()
        draw = ImageDraw.Draw(img)

        # ---- Build month list ----
        months = []
        y, m = period_start.year, period_start.month
        while (y, m) <= (period_end.year, period_end.month):
            months.append((y, m))
            if m == 12:
                y += 1
                m = 1
            else:
                m += 1

        num_months = max(1, len(months))
        cols = 31  # max days in any month

        # ---- Layout ----
        # Estimate label width so we reserve enough left margin
        scale = min(self.width, self.height) / 1080.0
        label_w_estimate = max(40, int(8 * 0.6 * self.label_font_size))
        label_pad = max(6, int(12 * scale))
        left_margin  = label_w_estimate + label_pad + max(10, int(16 * scale))
        right_margin = max(10, int(16 * scale))
        top_margin   = max(50, int(90 * scale))
        bottom_margin = max(40, int(70 * scale))

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

        # ---- Title (centered above grid) ----
        if title_text:
            bbox = draw.textbbox((0, 0), title_text, font=self.title_font)
            tw = bbox[2] - bbox[0]
            th = bbox[3] - bbox[1]
            tx = start_x + (grid_w - tw) // 2
            ty = max(10, start_y - th - max(15, int(25 * scale)))
            draw.text((tx + 2, ty + 2), title_text, fill=(0, 0, 0), font=self.title_font)
            draw.text((tx, ty), title_text, fill=theme.title_color, font=self.title_font)

        # ---- Weekly vertical separators (after day 7, 14, 21, 28) ----
        sep_w = 1 if dot_size < 6 else 2
        sep_glow_color = tuple(max(0, c - 8) for c in theme.separator_color)
        for week_boundary in (7, 14, 21, 28):
            sx = start_x + week_boundary * (dot_size + spacing) - spacing // 2
            # Glow lines flanking the separator
            draw.line([(sx - 1, start_y - 4), (sx - 1, start_y + grid_h + 4)],
                      fill=sep_glow_color, width=1)
            draw.line([(sx + 1, start_y - 4), (sx + 1, start_y + grid_h + 4)],
                      fill=sep_glow_color, width=1)
            # Main separator
            draw.line([(sx, start_y - 4), (sx, start_y + grid_h + 4)],
                      fill=theme.separator_color, width=sep_w)

        # ---- Filled-until date ----
        today = date.today()
        if today < period_start:
            filled_until = period_start - timedelta(days=1)
        elif today > period_end:
            filled_until = period_end
        else:
            filled_until = today

        # ---- Draw month rows ----
        filled_colors = theme.filled_colors
        empty_colors  = theme.empty_colors

        for row_idx, (yr, mo) in enumerate(months):
            days_in_month = calendar.monthrange(yr, mo)[1]

            # Month label (e.g., "Dec 2025")
            month_name = date(yr, mo, 1).strftime("%b %Y")
            lbbox = draw.textbbox((0, 0), month_name, font=self.label_font)
            lw = lbbox[2] - lbbox[0]
            lx = max(4, start_x - lw - label_pad)
            ly = start_y + row_idx * (dot_size + spacing) + (dot_size - (lbbox[3] - lbbox[1])) // 2
            draw.text((lx + 1, ly + 1), month_name, fill=(0, 0, 0), font=self.label_font)
            draw.text((lx, ly), month_name, fill=theme.label_color, font=self.label_font)

            for col_idx in range(cols):
                x = start_x + col_idx * (dot_size + spacing)
                y_px = start_y + row_idx * (dot_size + spacing)

                day_num = col_idx + 1
                cell_date = date(yr, mo, day_num) if day_num <= days_in_month else None

                # Week-group color index within the month row
                wg = (col_idx // 7) % len(filled_colors)

                # Disabled cells: outside month range or outside chosen period
                if cell_date is None or cell_date < period_start or cell_date > period_end:
                    draw.ellipse(
                        [x, y_px, x + dot_size, y_px + dot_size],
                        fill=theme.disabled_dot
                    )
                    continue

                is_filled = cell_date <= filled_until
                is_today = (cell_date == today and period_start <= today <= period_end)

                # ---- Dot rendering ----
                if is_today:
                    # Today: glowing highlight
                    glow_pad = max(3, dot_size // 2)
                    ring_pad = max(2, dot_size // 4)
                    draw.ellipse(
                        [x - glow_pad, y_px - glow_pad,
                         x + dot_size + glow_pad, y_px + dot_size + glow_pad],
                        fill=theme.today_glow
                    )
                    draw.ellipse(
                        [x - ring_pad, y_px - ring_pad,
                         x + dot_size + ring_pad, y_px + dot_size + ring_pad],
                        fill=theme.today_ring
                    )
                    dot_color = theme.today_dot
                elif is_filled:
                    fc = filled_colors[wg]
                    glow_pad = max(1, dot_size // 7)
                    glow_c = tuple(max(30, c - 40) for c in fc)
                    draw.ellipse(
                        [x - glow_pad, y_px - glow_pad,
                         x + dot_size + glow_pad, y_px + dot_size + glow_pad],
                        fill=glow_c
                    )
                    dot_color = fc
                else:
                    dot_color = empty_colors[wg]

                # The dot
                draw.ellipse(
                    [x, y_px, x + dot_size, y_px + dot_size],
                    fill=dot_color
                )

                # 3D highlight on filled dots (skip today's dot)
                if is_filled and not is_today:
                    hs = max(1, dot_size // 4)
                    hx = x + dot_size // 3
                    hy = y_px + dot_size // 4
                    draw.ellipse([hx, hy, hx + hs, hy + hs], fill=(255, 255, 255))

        # ---- Footer (centered below grid) ----
        if footer_text:
            bbox = draw.textbbox((0, 0), footer_text, font=self.footer_font)
            fw = bbox[2] - bbox[0]
            fx = start_x + (grid_w - fw) // 2
            fy = start_y + grid_h + max(15, int(25 * scale))
            draw.text((fx + 1, fy + 1), footer_text, fill=(0, 0, 0), font=self.footer_font)
            draw.text((fx, fy), footer_text, fill=theme.footer_color, font=self.footer_font)

        return img

    # ---- High-level calendar generators ----

    def generate_life_calendar(self, birth_date, output_path, custom_title=None):
        """
        Generate a Life Calendar wallpaper (52 weeks × 90 years).

        Args:
            birth_date:   date object for the birth date.
            output_path:  File path to save the PNG.
            custom_title: Optional title override (default: "Life Calendar").
        """
        (weeks_lived, total_weeks, weeks_remaining,
         days_lived, total_days, days_remaining) = self.calculate_life_weeks(birth_date)

        title = custom_title or "Life Calendar"

        # Footer with progress stats
        pct = weeks_lived * 100 // total_weeks if total_weeks > 0 else 0
        footer = f"{weeks_remaining:,}w left · {pct}%"

        img = self.draw_grid(
            filled_count=weeks_lived,
            total_count=total_weeks,
            title_text=title,
            footer_text=footer,
            grid_cols=52,
            grid_rows=90,
            current_day_index=None,   # life calendar works in weeks, not days
            dots_per_period=4,        # 4 weeks ≈ 1 month for color grouping
        )
        img.save(output_path, 'PNG')
        print(f"Life Calendar saved: {output_path}")
        print(f"  Weeks: {weeks_lived:,} / {total_weeks:,} ({pct}%)")
        print(f"  Days:  {days_lived:,} / {total_days:,}")
        print(f"  Theme: {self.theme}")

    def generate_year_calendar(self, output_path, start_date=None,
                               end_date=None, custom_title=None):
        """
        Generate a Year Calendar wallpaper (month-row layout, days 1–31).

        Args:
            output_path:  File path to save the PNG.
            start_date:   Period start (default: Jan 1 of current year).
            end_date:     Period end (default: Dec 31 of current year).
            custom_title: Optional title override.
        """
        (weeks_elapsed, total_weeks, weeks_remaining,
         days_elapsed, total_days, days_remaining) = self.calculate_year_weeks(
            start_date, end_date
        )

        today = date.today()
        period_start = start_date if start_date else date(today.year, 1, 1)
        period_end   = end_date   if end_date   else date(today.year, 12, 31)

        # Default title shows the date range
        if start_date and end_date:
            default_title = (f"{start_date.strftime('%b %d, %Y')} → "
                             f"{end_date.strftime('%b %d, %Y')}")
        else:
            default_title = "Year Calendar"

        title = custom_title or default_title

        # Footer: "Xd left · Y%"
        pct = days_elapsed * 100 // total_days if total_days > 0 else 0
        footer = f"{days_remaining}d left · {pct}%"

        img = self.draw_month_rows_year_calendar(
            period_start=period_start,
            period_end=period_end,
            title_text=title,
            footer_text=footer,
        )
        img.save(output_path, 'PNG')
        print(f"Year Calendar saved: {output_path}")
        print(f"  Days:  {days_elapsed} / {total_days} ({pct}%)")
        print(f"  Weeks: {weeks_elapsed} / {total_weeks}")
        print(f"  Theme: {self.theme}")


# =============================================================================
# WALLPAPER SETTER (Linux Mint / Cinnamon / MATE / XFCE / GNOME)
# =============================================================================

def set_wallpaper_linux_mint(image_path):
    """
    Set the desktop wallpaper on Linux using gsettings/xfconf.
    Supports Cinnamon, MATE, XFCE, and GNOME (fallback).

    Args:
        image_path: Path to the wallpaper image.

    Returns:
        True on success, False on failure.
    """
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
            # GNOME fallback
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
# CLI ENTRY POINT
# =============================================================================

def main():
    """Parse CLI arguments and generate wallpapers."""
    parser = argparse.ArgumentParser(
        description='Generate dynamic Life Calendar / Year Calendar wallpapers'
    )
    parser.add_argument(
        '--type', choices=['life', 'year', 'both'], default='both',
        help='Calendar type (default: both)'
    )
    parser.add_argument(
        '--birth-date', type=str,
        help='Birth date YYYY-MM-DD (required for life calendar)'
    )
    parser.add_argument('--output-dir', type=str, default='.', help='Output directory')
    parser.add_argument('--width',  type=int, default=1920, help='Image width (px)')
    parser.add_argument('--height', type=int, default=1080, help='Image height (px)')
    parser.add_argument('--set-wallpaper', action='store_true', help='Set as wallpaper')
    parser.add_argument('--life-output', type=str, default='life_calendar.png')
    parser.add_argument('--year-output', type=str, default='year_calendar.png')
    parser.add_argument('--title', type=str, default='', help='Custom title text')
    parser.add_argument('--year-start', type=str, help='Year calendar start YYYY-MM-DD')
    parser.add_argument('--year-end',   type=str, help='Year calendar end YYYY-MM-DD')

    args = parser.parse_args()

    # ---- Validate birth date ----
    birth_date = None
    if args.type in ('life', 'both'):
        if not args.birth_date:
            print("Error: --birth-date is required for life calendar")
            sys.exit(1)
        try:
            birth_date = datetime.strptime(args.birth_date, '%Y-%m-%d').date()
        except ValueError:
            print("Error: Invalid birth date format. Use YYYY-MM-DD")
            sys.exit(1)

    # ---- Validate year calendar dates ----
    year_start = year_end = None
    if args.type in ('year', 'both'):
        if args.year_start:
            try:
                year_start = datetime.strptime(args.year_start, '%Y-%m-%d').date()
            except ValueError:
                print("Error: Invalid --year-start format. Use YYYY-MM-DD")
                sys.exit(1)
        if args.year_end:
            try:
                year_end = datetime.strptime(args.year_end, '%Y-%m-%d').date()
            except ValueError:
                print("Error: Invalid --year-end format. Use YYYY-MM-DD")
                sys.exit(1)
        if year_start and year_end and year_start >= year_end:
            print("Error: Start date must be before end date")
            sys.exit(1)

    # ---- Setup ----
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    generator = LifeCalendarGenerator(width=args.width, height=args.height)
    custom_title = args.title or None

    # ---- Generate ----
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
