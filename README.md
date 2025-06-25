# DracoVed

DracoVed is a command-line toolkit for Vedic astrology research. It allows you to explore planetary positions using modern astronomical ephemerides and produces colourful terminal output thanks to the [`rich`](https://github.com/Textualize/rich) library.

## Features
- **N‑planet conjunction search** – list all days where N or more bodies (including Rahu and Ketu) occupy the same sidereal sign.
- **Specific pair search** – find every date two chosen planets meet in a sign.
- **D1 birth chart output** – generate a basic birth chart from a date, time and location.
- **Transit viewer** – review sign changes for all planets in a given year.

## Installation
1. Install Python 3.8 or newer.
2. Install the required packages:
   ```bash
   pip install rich skyfield swisseph geopy pytz timezonefinder
   ```
3. Download Swiss Ephemeris `.se1` files and the `de440.bsp` JPL ephemeris and place them in this directory.

## Running
Run the interactive menu:
```bash
python DracoVed_v1.py
```
Follow the prompts to choose a feature.

## Repository Layout
- `DracoVed_v1.py` – entry point and text menu.
- `features.py` – implementations of conjunction searches, D1 chart and transit viewer.
- `astro_utils.py` – astronomy helper functions.
- `display_utils.py` – rich-console helpers.
- `config.py` – constants such as ayanamsa and planet names.

## Notes
- The program expects ephemeris files in the same folder. Without them, calculations will fail.
- Output uses Unicode and ANSI colours. Use a compatible terminal for best results.

---
Created by Mahir, 2025.
