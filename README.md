# DracoVed

DracoVed is a Vedic astrology research tool for finding planetary conjunctions and generating D1 (Lagna) birth charts using modern astronomical ephemerides.

## Features
- **N-Planet Conjunction Search:** Find all dates when N or more planets (including Rahu/Ketu) are in the same sidereal sign.
- **Pairwise Conjunction Search:** Find all dates when any two specific planets are conjunct in the same sign.
- **D1 Birth Chart Generator:** Enter birth details and location to generate a detailed Vedic D1 chart, including ascendant, planetary positions, and house distribution.
- **Timezone and Geolocation Support:** Automatic timezone detection for birth location (with manual fallback).
- **Rich Terminal Output:** Beautiful, color-coded tables and panels for easy reading.

## Requirements
- Python 3.8+
- Packages: `rich`, `skyfield`, `swisseph`, `geopy`, `pytz`, `timezonefinder`
- Swiss Ephemeris `.se1` files and `de440.bsp` ephemeris file in the script directory

## Usage
1. Install dependencies:
   ```cmd
   pip install rich skyfield swisseph geopy pytz timezonefinder
   ```
2. Run the program:
   ```cmd
   python DracoVed_v1.py
   ```
3. Follow the menu prompts to use conjunction search or generate a D1 chart.

## File Structure
- `DracoVed_v1.py` — Main entry point (menu/CLI)
- `features.py` — Main features (conjunctions, D1 chart)
- `astro_utils.py` — Astronomy and calculation helpers
- `display_utils.py` — Rich output helpers
- `config.py` — Configuration and constants

## Notes
- Make sure the required ephemeris files are present in the same directory as the scripts.
- For best results, use a terminal that supports Unicode and ANSI colors.

---
Created by Mahir, 2025.
