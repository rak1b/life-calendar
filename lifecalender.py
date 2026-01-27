#!/usr/bin/env python3
"""
Life Calendar Wallpaper Generator for Linux Mint
Generates minimalist wallpapers showing life progress in weeks or year progress.
"""

import os
import sys
import calendar
import random
import math
from datetime import datetime, date, timedelta
from PIL import Image, ImageDraw, ImageFont
import subprocess
import argparse
from pathlib import Path

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False


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
    
    def get_color_palettes(self):
        """
        Get 100 professionally researched color palettes for dark/black backgrounds.
        Based on web research and proven design systems:
        - Algorithmic gradient generation (twallpaper, wallendar projects)
        - Complementary color theory for dark UIs
        - Material Design and modern UI frameworks
        - High contrast ratios for readability
        - Smooth multi-color gradient transitions
        
        Returns:
            List of color palette dictionaries with 4 corner colors for bilinear gradients
        """
        return [
            # Deep Blue + Cyan (1-10) - High contrast, modern tech aesthetic
            {'top_left': (15, 25, 42), 'top_right': (12, 32, 48), 'bottom_left': (8, 14, 24), 'bottom_right': (6, 20, 30)},
            {'top_left': (18, 28, 45), 'top_right': (15, 35, 50), 'bottom_left': (10, 16, 26), 'bottom_right': (8, 22, 32)},
            {'top_left': (12, 22, 38), 'top_right': (10, 30, 45), 'bottom_left': (7, 12, 22), 'bottom_right': (5, 18, 28)},
            {'top_left': (20, 30, 48), 'top_right': (18, 38, 52), 'bottom_left': (11, 18, 28), 'bottom_right': (9, 24, 34)},
            {'top_left': (14, 24, 40), 'top_right': (11, 28, 46), 'bottom_left': (8, 13, 23), 'bottom_right': (6, 19, 29)},
            {'top_left': (22, 32, 50), 'top_right': (20, 40, 54), 'bottom_left': (12, 20, 30), 'bottom_right': (10, 26, 36)},
            {'top_left': (16, 26, 43), 'top_right': (13, 33, 49), 'bottom_left': (9, 15, 25), 'bottom_right': (7, 21, 31)},
            {'top_left': (13, 23, 39), 'top_right': (11, 31, 47), 'bottom_left': (7, 12, 22), 'bottom_right': (5, 18, 28)},
            {'top_left': (19, 29, 46), 'top_right': (17, 37, 51), 'bottom_left': (10, 17, 27), 'bottom_right': (8, 23, 33)},
            {'top_left': (11, 21, 37), 'top_right': (9, 29, 44), 'bottom_left': (6, 11, 21), 'bottom_right': (4, 17, 27)},
            
            # Purple + Magenta (11-20) - Vibrant yet sophisticated
            {'top_left': (32, 18, 42), 'top_right': (38, 22, 48), 'bottom_left': (18, 10, 24), 'bottom_right': (22, 14, 30)},
            {'top_left': (35, 20, 45), 'top_right': (41, 24, 50), 'bottom_left': (20, 11, 26), 'bottom_right': (24, 15, 32)},
            {'top_left': (29, 16, 39), 'top_right': (35, 20, 45), 'bottom_left': (16, 9, 22), 'bottom_right': (20, 13, 28)},
            {'top_left': (38, 22, 48), 'top_right': (44, 26, 52), 'bottom_left': (22, 12, 28), 'bottom_right': (26, 16, 34)},
            {'top_left': (26, 14, 36), 'top_right': (32, 18, 42), 'bottom_left': (14, 8, 20), 'bottom_right': (18, 12, 26)},
            {'top_left': (41, 24, 50), 'top_right': (47, 28, 54), 'bottom_left': (24, 13, 30), 'bottom_right': (28, 17, 36)},
            {'top_left': (33, 19, 43), 'top_right': (39, 23, 49), 'bottom_left': (19, 10, 25), 'bottom_right': (23, 14, 31)},
            {'top_left': (30, 17, 40), 'top_right': (36, 21, 46), 'bottom_left': (17, 9, 23), 'bottom_right': (21, 13, 29)},
            {'top_left': (36, 21, 46), 'top_right': (42, 25, 51), 'bottom_left': (21, 11, 27), 'bottom_right': (25, 15, 33)},
            {'top_left': (27, 15, 37), 'top_right': (33, 19, 43), 'bottom_left': (15, 8, 21), 'bottom_right': (19, 12, 27)},
            
            # Teal + Orange (21-30) - Complementary colors with strong visual appeal
            {'top_left': (14, 38, 42), 'top_right': (42, 28, 18), 'bottom_left': (8, 20, 24), 'bottom_right': (24, 16, 10)},
            {'top_left': (16, 40, 44), 'top_right': (45, 30, 20), 'bottom_left': (9, 21, 25), 'bottom_right': (26, 17, 11)},
            {'top_left': (12, 36, 40), 'top_right': (39, 26, 16), 'bottom_left': (7, 19, 23), 'bottom_right': (22, 15, 9)},
            {'top_left': (18, 42, 46), 'top_right': (48, 32, 22), 'bottom_left': (10, 22, 26), 'bottom_right': (28, 18, 12)},
            {'top_left': (10, 34, 38), 'top_right': (36, 24, 14), 'bottom_left': (6, 18, 22), 'bottom_right': (20, 14, 8)},
            {'top_left': (20, 44, 48), 'top_right': (50, 34, 24), 'bottom_left': (11, 23, 27), 'bottom_right': (30, 19, 13)},
            {'top_left': (15, 39, 43), 'top_right': (43, 29, 19), 'bottom_left': (8, 20, 24), 'bottom_right': (25, 16, 10)},
            {'top_left': (13, 37, 41), 'top_right': (41, 27, 17), 'bottom_left': (7, 19, 23), 'bottom_right': (23, 15, 9)},
            {'top_left': (17, 41, 45), 'top_right': (46, 31, 21), 'bottom_left': (9, 21, 25), 'bottom_right': (27, 17, 11)},
            {'top_left': (11, 35, 39), 'top_right': (38, 25, 15), 'bottom_left': (6, 18, 22), 'bottom_right': (21, 14, 8)},
            
            # Navy + Gold (31-40) - Elegant and premium feel
            {'top_left': (12, 18, 35), 'top_right': (42, 35, 18), 'bottom_left': (7, 10, 20), 'bottom_right': (24, 20, 10)},
            {'top_left': (14, 20, 38), 'top_right': (45, 38, 20), 'bottom_left': (8, 11, 22), 'bottom_right': (26, 21, 11)},
            {'top_left': (10, 16, 32), 'top_right': (39, 32, 16), 'bottom_left': (6, 9, 18), 'bottom_right': (22, 18, 9)},
            {'top_left': (16, 22, 40), 'top_right': (48, 40, 22), 'bottom_left': (9, 12, 24), 'bottom_right': (28, 22, 12)},
            {'top_left': (8, 14, 30), 'top_right': (36, 30, 14), 'bottom_left': (5, 8, 17), 'bottom_right': (20, 17, 8)},
            {'top_left': (18, 24, 42), 'top_right': (50, 42, 24), 'bottom_left': (10, 13, 25), 'bottom_right': (30, 23, 13)},
            {'top_left': (13, 19, 36), 'top_right': (43, 36, 19), 'bottom_left': (7, 10, 20), 'bottom_right': (25, 20, 10)},
            {'top_left': (11, 17, 33), 'top_right': (41, 34, 17), 'bottom_left': (6, 9, 18), 'bottom_right': (23, 19, 9)},
            {'top_left': (15, 21, 39), 'top_right': (46, 39, 21), 'bottom_left': (8, 11, 22), 'bottom_right': (27, 21, 11)},
            {'top_left': (9, 15, 31), 'top_right': (37, 31, 15), 'bottom_left': (5, 8, 17), 'bottom_right': (21, 18, 8)},
            
            # Deep Green + Lime (41-50) - Natural yet energetic
            {'top_left': (10, 32, 20), 'top_right': (28, 42, 18), 'bottom_left': (6, 18, 11), 'bottom_right': (16, 24, 10)},
            {'top_left': (12, 34, 22), 'top_right': (30, 44, 20), 'bottom_left': (7, 19, 12), 'bottom_right': (17, 25, 11)},
            {'top_left': (8, 30, 18), 'top_right': (26, 40, 16), 'bottom_left': (5, 17, 10), 'bottom_right': (15, 23, 9)},
            {'top_left': (14, 36, 24), 'top_right': (32, 46, 22), 'bottom_left': (8, 20, 13), 'bottom_right': (18, 26, 12)},
            {'top_left': (6, 28, 16), 'top_right': (24, 38, 14), 'bottom_left': (4, 16, 9), 'bottom_right': (14, 22, 8)},
            {'top_left': (16, 38, 26), 'top_right': (34, 48, 24), 'bottom_left': (9, 21, 14), 'bottom_right': (19, 27, 13)},
            {'top_left': (11, 33, 21), 'top_right': (29, 43, 19), 'bottom_left': (6, 18, 11), 'bottom_right': (16, 24, 10)},
            {'top_left': (9, 31, 19), 'top_right': (27, 41, 17), 'bottom_left': (5, 17, 10), 'bottom_right': (15, 23, 9)},
            {'top_left': (13, 35, 23), 'top_right': (31, 45, 21), 'bottom_left': (7, 19, 12), 'bottom_right': (17, 25, 11)},
            {'top_left': (7, 29, 17), 'top_right': (25, 39, 15), 'bottom_left': (4, 16, 9), 'bottom_right': (14, 22, 8)},
            
            # Indigo + Electric Blue (51-60) - Modern and sleek
            {'top_left': (22, 18, 38), 'top_right': (15, 28, 48), 'bottom_left': (12, 10, 22), 'bottom_right': (8, 16, 30)},
            {'top_left': (24, 20, 40), 'top_right': (17, 30, 50), 'bottom_left': (13, 11, 23), 'bottom_right': (9, 17, 32)},
            {'top_left': (20, 16, 36), 'top_right': (13, 26, 46), 'bottom_left': (11, 9, 21), 'bottom_right': (7, 15, 29)},
            {'top_left': (26, 22, 42), 'top_right': (19, 32, 52), 'bottom_left': (14, 12, 24), 'bottom_right': (10, 18, 33)},
            {'top_left': (18, 14, 34), 'top_right': (11, 24, 44), 'bottom_left': (10, 8, 20), 'bottom_right': (6, 14, 28)},
            {'top_left': (28, 24, 44), 'top_right': (21, 34, 54), 'bottom_left': (15, 13, 25), 'bottom_right': (11, 19, 34)},
            {'top_left': (23, 19, 39), 'top_right': (16, 29, 49), 'bottom_left': (12, 10, 22), 'bottom_right': (8, 16, 30)},
            {'top_left': (21, 17, 37), 'top_right': (14, 27, 47), 'bottom_left': (11, 9, 21), 'bottom_right': (7, 15, 29)},
            {'top_left': (25, 21, 41), 'top_right': (18, 31, 51), 'bottom_left': (13, 11, 23), 'bottom_right': (9, 17, 32)},
            {'top_left': (19, 15, 35), 'top_right': (12, 25, 45), 'bottom_left': (10, 8, 20), 'bottom_right': (6, 14, 28)},
            
            # Charcoal + Neon Pink (61-70) - High contrast, contemporary
            {'top_left': (24, 24, 28), 'top_right': (48, 20, 38), 'bottom_left': (13, 13, 16), 'bottom_right': (28, 11, 22)},
            {'top_left': (26, 26, 30), 'top_right': (50, 22, 40), 'bottom_left': (14, 14, 17), 'bottom_right': (30, 12, 23)},
            {'top_left': (22, 22, 26), 'top_right': (46, 18, 36), 'bottom_left': (12, 12, 15), 'bottom_right': (26, 10, 21)},
            {'top_left': (28, 28, 32), 'top_right': (52, 24, 42), 'bottom_left': (15, 15, 18), 'bottom_right': (32, 13, 24)},
            {'top_left': (20, 20, 24), 'top_right': (44, 16, 34), 'bottom_left': (11, 11, 14), 'bottom_right': (24, 9, 20)},
            {'top_left': (30, 30, 34), 'top_right': (54, 26, 44), 'bottom_left': (16, 16, 19), 'bottom_right': (34, 14, 25)},
            {'top_left': (25, 25, 29), 'top_right': (49, 21, 39), 'bottom_left': (13, 13, 16), 'bottom_right': (29, 11, 22)},
            {'top_left': (23, 23, 27), 'top_right': (47, 19, 37), 'bottom_left': (12, 12, 15), 'bottom_right': (27, 10, 21)},
            {'top_left': (27, 27, 31), 'top_right': (51, 23, 41), 'bottom_left': (14, 14, 17), 'bottom_right': (31, 12, 23)},
            {'top_left': (21, 21, 25), 'top_right': (45, 17, 35), 'bottom_left': (11, 11, 14), 'bottom_right': (25, 9, 20)},
            
            # Dark Slate + Cyan (71-80) - Professional and calm
            {'top_left': (22, 26, 30), 'top_right': (12, 32, 42), 'bottom_left': (12, 14, 17), 'bottom_right': (6, 18, 25)},
            {'top_left': (24, 28, 32), 'top_right': (14, 34, 44), 'bottom_left': (13, 15, 18), 'bottom_right': (7, 19, 26)},
            {'top_left': (20, 24, 28), 'top_right': (10, 30, 40), 'bottom_left': (11, 13, 16), 'bottom_right': (5, 17, 24)},
            {'top_left': (26, 30, 34), 'top_right': (16, 36, 46), 'bottom_left': (14, 16, 19), 'bottom_right': (8, 20, 27)},
            {'top_left': (18, 22, 26), 'top_right': (8, 28, 38), 'bottom_left': (10, 12, 15), 'bottom_right': (4, 16, 23)},
            {'top_left': (28, 32, 36), 'top_right': (18, 38, 48), 'bottom_left': (15, 17, 20), 'bottom_right': (9, 21, 28)},
            {'top_left': (23, 27, 31), 'top_right': (13, 33, 43), 'bottom_left': (12, 14, 17), 'bottom_right': (6, 18, 25)},
            {'top_left': (21, 25, 29), 'top_right': (11, 31, 41), 'bottom_left': (11, 13, 16), 'bottom_right': (5, 17, 24)},
            {'top_left': (25, 29, 33), 'top_right': (15, 35, 45), 'bottom_left': (13, 15, 18), 'bottom_right': (7, 19, 26)},
            {'top_left': (19, 23, 27), 'top_right': (9, 29, 39), 'bottom_left': (10, 12, 15), 'bottom_right': (4, 16, 23)},
            
            # Deep Purple + Electric Violet (81-90) - Rich and immersive
            {'top_left': (28, 14, 38), 'top_right': (42, 22, 52), 'bottom_left': (16, 8, 22), 'bottom_right': (24, 12, 32)},
            {'top_left': (30, 16, 40), 'top_right': (44, 24, 54), 'bottom_left': (17, 9, 23), 'bottom_right': (25, 13, 33)},
            {'top_left': (26, 12, 36), 'top_right': (40, 20, 50), 'bottom_left': (15, 7, 21), 'bottom_right': (23, 11, 31)},
            {'top_left': (32, 18, 42), 'top_right': (46, 26, 56), 'bottom_left': (18, 10, 24), 'bottom_right': (26, 14, 34)},
            {'top_left': (24, 10, 34), 'top_right': (38, 18, 48), 'bottom_left': (14, 6, 20), 'bottom_right': (22, 10, 30)},
            {'top_left': (34, 20, 44), 'top_right': (48, 28, 58), 'bottom_left': (19, 11, 25), 'bottom_right': (27, 15, 35)},
            {'top_left': (29, 15, 39), 'top_right': (43, 23, 53), 'bottom_left': (16, 8, 22), 'bottom_right': (24, 12, 32)},
            {'top_left': (27, 13, 37), 'top_right': (41, 21, 51), 'bottom_left': (15, 7, 21), 'bottom_right': (23, 11, 31)},
            {'top_left': (31, 17, 41), 'top_right': (45, 25, 55), 'bottom_left': (17, 9, 23), 'bottom_right': (25, 13, 33)},
            {'top_left': (25, 11, 35), 'top_right': (39, 19, 49), 'bottom_left': (14, 6, 20), 'bottom_right': (22, 10, 30)},
            
            # Dark Teal + Coral (91-100) - Balanced warm-cool contrast
            {'top_left': (12, 36, 38), 'top_right': (44, 28, 24), 'bottom_left': (7, 20, 22), 'bottom_right': (25, 16, 14)},
            {'top_left': (14, 38, 40), 'top_right': (46, 30, 26), 'bottom_left': (8, 21, 23), 'bottom_right': (26, 17, 15)},
            {'top_left': (10, 34, 36), 'top_right': (42, 26, 22), 'bottom_left': (6, 19, 21), 'bottom_right': (24, 15, 13)},
            {'top_left': (16, 40, 42), 'top_right': (48, 32, 28), 'bottom_left': (9, 22, 24), 'bottom_right': (28, 18, 16)},
            {'top_left': (8, 32, 34), 'top_right': (40, 24, 20), 'bottom_left': (5, 18, 20), 'bottom_right': (22, 14, 12)},
            {'top_left': (18, 42, 44), 'top_right': (50, 34, 30), 'bottom_left': (10, 23, 25), 'bottom_right': (30, 19, 17)},
            {'top_left': (13, 37, 39), 'top_right': (45, 29, 25), 'bottom_left': (7, 20, 22), 'bottom_right': (25, 16, 14)},
            {'top_left': (11, 35, 37), 'top_right': (43, 27, 23), 'bottom_left': (6, 19, 21), 'bottom_right': (24, 15, 13)},
            {'top_left': (15, 39, 41), 'top_right': (47, 31, 27), 'bottom_left': (8, 21, 23), 'bottom_right': (26, 17, 15)},
            {'top_left': (9, 33, 35), 'top_right': (41, 25, 21), 'bottom_left': (5, 18, 20), 'bottom_right': (23, 14, 12)},
        ]
        
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
        # Create image with beautiful sophisticated background
        img = Image.new('RGB', (self.width, self.height), self.bg_color)
        draw = ImageDraw.Draw(img)
        
        # Create beautiful multi-layer gradient background with vibrant colors (OPTIMIZED)
        if HAS_NUMPY:
            # Get one of 100 beautiful color palettes optimized for dark UI
            color_palettes = self.get_color_palettes()
            
            # Mix 2-3 color palettes for more noticeable, vibrant gradients
            num_palettes = random.choice([2, 3])  # Randomly choose 2 or 3 palettes to mix
            selected_palettes = random.sample(color_palettes, num_palettes)
            
            # Blend weights for mixing (sum to 1.0)
            if num_palettes == 2:
                weights = [0.5, 0.5]  # Equal blend
            else:  # 3 palettes
                w1 = random.uniform(0.3, 0.5)
                w2 = random.uniform(0.25, 0.4)
                w3 = 1.0 - w1 - w2
                weights = [w1, w2, w3]
            
            # Blend the palettes together for each corner
            def blend_corner(corner_name):
                blended = np.array([0.0, 0.0, 0.0], dtype=np.float32)
                for palette, weight in zip(selected_palettes, weights):
                    blended += np.array(palette[corner_name], dtype=np.float32) * weight
                return blended
            
            # Blend all corners from multiple palettes
            top_left_base = blend_corner('top_left')
            top_right_base = blend_corner('top_right')
            bottom_left_base = blend_corner('bottom_left')
            bottom_right_base = blend_corner('bottom_right')
            
            # Apply slight variations for uniqueness and boost vibrancy
            variation = random.randint(-2, 2)
            boost = random.uniform(1.0, 1.15)  # Slight boost to make colors more noticeable
            
            top_left = np.clip((top_left_base + variation) * boost, 10, 55)
            top_right = np.clip((top_right_base + random.randint(-2, 2)) * boost, 10, 55)
            bottom_left = np.clip((bottom_left_base + variation) * boost, 5, 35)
            bottom_right = np.clip((bottom_right_base + random.randint(-2, 2)) * boost, 5, 35)
            
            # Ensure proper dtype
            top_left = top_left.astype(np.float32)
            top_right = top_right.astype(np.float32)
            bottom_left = bottom_left.astype(np.float32)
            bottom_right = bottom_right.astype(np.float32)
            
            # VECTORIZED gradient generation (much faster!)
            center_x, center_y = self.width / 2, self.height / 2
            max_dist = math.sqrt(center_x**2 + center_y**2)
            
            # Create coordinate grids (vectorized)
            y_coords, x_coords = np.mgrid[0:self.height, 0:self.width].astype(np.float32)
            nx = x_coords / self.width
            ny = y_coords / self.height
            
            # Bilinear interpolation (vectorized)
            top = top_left[:, None, None] * (1 - nx) + top_right[:, None, None] * nx
            bottom = bottom_left[:, None, None] * (1 - nx) + bottom_right[:, None, None] * nx
            color = top * (1 - ny) + bottom * ny
            
            # Radial distance (vectorized)
            dist = np.sqrt((x_coords - center_x)**2 + (y_coords - center_y)**2)
            
            # Vignette effect (vectorized) - reduced to let mixed colors show through
            vignette = 1.0 - (dist / max_dist) * 0.15  # Less darkening to preserve vibrant mixed colors
            color = color * vignette
            
            # Center glow effect (vectorized) - enhanced for more vibrant center
            center_glow = 1.0 + (1.0 - dist / max_dist) * 0.2  # More noticeable brightening for mixed colors
            color = np.clip(color * center_glow, 0, 255)
            
            # Subtle noise for texture (vectorized)
            noise = np.random.normal(1.0, 0.025, (3, self.height, self.width)).astype(np.float32)
            color = np.clip(color * noise, 0, 255)
            
            # Transpose to (height, width, 3) and convert to uint8
            img_array = color.transpose(1, 2, 0).astype(np.uint8)
            
            # Convert numpy array to PIL Image
            img = Image.fromarray(img_array, 'RGB')
            draw = ImageDraw.Draw(img)
        else:
            # Fallback: Enhanced gradient without numpy (randomized colors)
            base_dark = 10 + random.randint(0, 8)
            hue_shift_1 = random.randint(-5, 5)
            hue_shift_2 = random.randint(-5, 5)
            top_base = 20 + random.randint(0, 12)
            
            top_left = (
                max(8, min(45, top_base + hue_shift_1)),
                max(8, min(45, top_base + random.randint(2, 6))),
                max(8, min(45, top_base + random.randint(4, 8)))
            )
            top_right = (
                max(8, min(45, top_base + random.randint(2, 6))),
                max(8, min(45, top_base + hue_shift_2)),
                max(8, min(45, top_base + random.randint(2, 6)))
            )
            bottom_left = (
                max(5, min(25, base_dark + hue_shift_1)),
                max(5, min(25, base_dark + random.randint(2, 6))),
                max(5, min(25, base_dark + random.randint(4, 8)))
            )
            bottom_right = (
                max(5, min(25, base_dark + random.randint(2, 6))),
                max(5, min(25, base_dark + hue_shift_2)),
                max(5, min(25, base_dark + random.randint(2, 6)))
            )
            
            chunk_size = max(1, self.height // 200)
            for chunk_start in range(0, self.height, chunk_size):
                chunk_end = min(chunk_start + chunk_size, self.height)
                y_center = (chunk_start + chunk_end) // 2
                ny = y_center / self.height
                
                # Interpolate top and bottom
                top_r = int(top_left[0] * (1 - ny) + top_right[0] * ny)
                top_g = int(top_left[1] * (1 - ny) + top_right[1] * ny)
                top_b = int(top_left[2] * (1 - ny) + top_right[2] * ny)
                bottom_r = int(bottom_left[0] * (1 - ny) + bottom_right[0] * ny)
                bottom_g = int(bottom_left[1] * (1 - ny) + bottom_right[1] * ny)
                bottom_b = int(bottom_left[2] * (1 - ny) + bottom_right[2] * ny)
                
                # Draw horizontal gradient
                for x in range(0, self.width, 5):
                    nx = x / self.width
                    r = int(top_r * (1 - nx) + bottom_r * nx)
                    g = int(top_g * (1 - nx) + bottom_g * nx)
                    b = int(top_b * (1 - nx) + bottom_b * nx)
                    draw.rectangle([(x, chunk_start), (min(x + 5, self.width), chunk_end)], fill=(r, g, b))
        
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

        # Create beautiful multi-layer gradient background with vibrant colors (OPTIMIZED)
        if HAS_NUMPY:
            # Get one of 100 beautiful color palettes optimized for dark UI
            color_palettes = self.get_color_palettes()
            
            # Mix 2-3 color palettes for more noticeable, vibrant gradients
            num_palettes = random.choice([2, 3])  # Randomly choose 2 or 3 palettes to mix
            selected_palettes = random.sample(color_palettes, num_palettes)
            
            # Blend weights for mixing (sum to 1.0)
            if num_palettes == 2:
                weights = [0.5, 0.5]  # Equal blend
            else:  # 3 palettes
                w1 = random.uniform(0.3, 0.5)
                w2 = random.uniform(0.25, 0.4)
                w3 = 1.0 - w1 - w2
                weights = [w1, w2, w3]
            
            # Blend the palettes together for each corner
            def blend_corner(corner_name):
                blended = np.array([0.0, 0.0, 0.0], dtype=np.float32)
                for palette, weight in zip(selected_palettes, weights):
                    blended += np.array(palette[corner_name], dtype=np.float32) * weight
                return blended
            
            # Blend all corners from multiple palettes
            top_left_base = blend_corner('top_left')
            top_right_base = blend_corner('top_right')
            bottom_left_base = blend_corner('bottom_left')
            bottom_right_base = blend_corner('bottom_right')
            
            # Apply slight variations for uniqueness and boost vibrancy
            variation = random.randint(-2, 2)
            boost = random.uniform(1.0, 1.15)  # Slight boost to make colors more noticeable
            
            top_left = np.clip((top_left_base + variation) * boost, 10, 55)
            top_right = np.clip((top_right_base + random.randint(-2, 2)) * boost, 10, 55)
            bottom_left = np.clip((bottom_left_base + variation) * boost, 5, 35)
            bottom_right = np.clip((bottom_right_base + random.randint(-2, 2)) * boost, 5, 35)
            
            # Ensure proper dtype
            top_left = top_left.astype(np.float32)
            top_right = top_right.astype(np.float32)
            bottom_left = bottom_left.astype(np.float32)
            bottom_right = bottom_right.astype(np.float32)
            
            # VECTORIZED gradient generation (much faster!)
            center_x, center_y = self.width / 2, self.height / 2
            max_dist = math.sqrt(center_x**2 + center_y**2)
            
            # Create coordinate grids (vectorized)
            y_coords, x_coords = np.mgrid[0:self.height, 0:self.width].astype(np.float32)
            nx = x_coords / self.width
            ny = y_coords / self.height
            
            # Bilinear interpolation (vectorized)
            top = top_left[:, None, None] * (1 - nx) + top_right[:, None, None] * nx
            bottom = bottom_left[:, None, None] * (1 - nx) + bottom_right[:, None, None] * nx
            color = top * (1 - ny) + bottom * ny
            
            # Radial distance (vectorized)
            dist = np.sqrt((x_coords - center_x)**2 + (y_coords - center_y)**2)
            
            # Vignette effect (vectorized) - reduced to let mixed colors show through
            vignette = 1.0 - (dist / max_dist) * 0.15  # Less darkening to preserve vibrant mixed colors
            color = color * vignette
            
            # Center glow effect (vectorized) - enhanced for more vibrant center
            center_glow = 1.0 + (1.0 - dist / max_dist) * 0.2  # More noticeable brightening for mixed colors
            color = np.clip(color * center_glow, 0, 255)
            
            # Subtle noise for texture (vectorized)
            noise = np.random.normal(1.0, 0.025, (3, self.height, self.width)).astype(np.float32)
            color = np.clip(color * noise, 0, 255)
            
            # Transpose to (height, width, 3) and convert to uint8
            img_array = color.transpose(1, 2, 0).astype(np.uint8)
            
            # Convert numpy array to PIL Image
            img = Image.fromarray(img_array, 'RGB')
            draw = ImageDraw.Draw(img)
        else:
            # Fallback: Enhanced gradient without numpy (randomized colors)
            base_dark = 10 + random.randint(0, 8)
            hue_shift_1 = random.randint(-5, 5)
            hue_shift_2 = random.randint(-5, 5)
            top_base = 20 + random.randint(0, 12)
            
            top_left = (
                max(8, min(45, top_base + hue_shift_1)),
                max(8, min(45, top_base + random.randint(2, 6))),
                max(8, min(45, top_base + random.randint(4, 8)))
            )
            top_right = (
                max(8, min(45, top_base + random.randint(2, 6))),
                max(8, min(45, top_base + hue_shift_2)),
                max(8, min(45, top_base + random.randint(2, 6)))
            )
            bottom_left = (
                max(5, min(25, base_dark + hue_shift_1)),
                max(5, min(25, base_dark + random.randint(2, 6))),
                max(5, min(25, base_dark + random.randint(4, 8)))
            )
            bottom_right = (
                max(5, min(25, base_dark + random.randint(2, 6))),
                max(5, min(25, base_dark + hue_shift_2)),
                max(5, min(25, base_dark + random.randint(2, 6)))
            )
            
            chunk_size = max(1, self.height // 200)
            for chunk_start in range(0, self.height, chunk_size):
                chunk_end = min(chunk_start + chunk_size, self.height)
                y_center = (chunk_start + chunk_end) // 2
                ny = y_center / self.height
                
                # Interpolate top and bottom
                top_r = int(top_left[0] * (1 - ny) + top_right[0] * ny)
                top_g = int(top_left[1] * (1 - ny) + top_right[1] * ny)
                top_b = int(top_left[2] * (1 - ny) + top_right[2] * ny)
                bottom_r = int(bottom_left[0] * (1 - ny) + bottom_right[0] * ny)
                bottom_g = int(bottom_left[1] * (1 - ny) + bottom_right[1] * ny)
                bottom_b = int(bottom_left[2] * (1 - ny) + bottom_right[2] * ny)
                
                # Draw horizontal gradient
                for x in range(0, self.width, 5):
                    nx = x / self.width
                    r = int(top_r * (1 - nx) + bottom_r * nx)
                    g = int(top_g * (1 - nx) + bottom_g * nx)
                    b = int(top_b * (1 - nx) + bottom_b * nx)
                    draw.rectangle([(x, chunk_start), (min(x + 5, self.width), chunk_end)], fill=(r, g, b))

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

        # Month labels on the left (enhanced with subtle shadow)
        label_color = (200, 200, 210)  # Brighter for better visibility
        label_padding = 18

        # Draw weekly separators (vertical) for readability: after day 7, 14, 21, 28
        # Enhanced separators with subtle glow effect
        separator_color = (70, 70, 75)
        separator_glow = (50, 50, 55)  # Slightly darker for depth
        for week_boundary in (7, 14, 21, 28):
            sep_x = start_x + week_boundary * (self.dot_size + self.spacing) - (self.spacing // 2)
            # Draw subtle glow behind separator
            draw.line([(sep_x - 1, start_y - 6), (sep_x - 1, start_y + grid_height + 6)], fill=separator_glow, width=1)
            draw.line([(sep_x + 1, start_y - 6), (sep_x + 1, start_y + grid_height + 6)], fill=separator_glow, width=1)
            # Main separator line
            draw.line([(sep_x, start_y - 6), (sep_x, start_y + grid_height + 6)], fill=separator_color, width=2)

        for row_idx, (y, m) in enumerate(months):
            days_in_month = calendar.monthrange(y, m)[1]

            # Label like "Dec 2025" with subtle shadow for depth
            month_name = date(y, m, 1).strftime("%b %Y")
            label_bbox = draw.textbbox((0, 0), month_name, font=label_font)
            label_width = label_bbox[2] - label_bbox[0]
            label_x = max(20, start_x - label_width - label_padding)
            label_y = start_y + row_idx * (self.dot_size + self.spacing) - 2
            # Draw shadow first
            draw.text((label_x + 1, label_y + 1), month_name, fill=(0, 0, 0), font=label_font)
            # Draw main text
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

                # Add subtle glow to filled dots for modern look (except today)
                if is_filled and not (cell_date == today and period_start <= today <= period_end):
                    glow_pad = 2
                    glow_color_r = max(40, dot_color[0] - 30)
                    glow_color_g = max(40, dot_color[1] - 30)
                    glow_color_b = max(40, dot_color[2] - 30)
                    draw.ellipse(
                        [x - glow_pad, y_px - glow_pad,
                         x + self.dot_size + glow_pad, y_px + self.dot_size + glow_pad],
                        fill=(glow_color_r, glow_color_g, glow_color_b),
                        outline=None
                    )
                
                # Draw dot
                draw.ellipse([x, y_px, x + self.dot_size, y_px + self.dot_size], fill=dot_color, outline=None)
                
                # Add subtle highlight to filled dots for depth (modern 3D effect)
                if is_filled and not (cell_date == today and period_start <= today <= period_end):
                    highlight_size = self.dot_size // 3
                    highlight_x = x + self.dot_size // 3
                    highlight_y = y_px + self.dot_size // 3
                    draw.ellipse(
                        [highlight_x, highlight_y,
                         highlight_x + highlight_size, highlight_y + highlight_size],
                        fill=(255, 255, 255),
                        outline=None
                    )

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
