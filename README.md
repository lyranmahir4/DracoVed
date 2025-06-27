# DracoVed

DracoVed is a command line toolkit for Vedic astrology research. It uses modern ephemerides from Skyfield and the Swiss Ephemeris to compute accurate sidereal positions and offers several interactive features via a rich terminal interface.

## Features
- **Multi-Planet Conjunction Search** – scan any time range for dates when a specified number of planets share the same sidereal sign. Rahu and Ketu are supported.
- **Pairwise Conjunctions** – list all dates when two chosen bodies meet in a sign, along with their degrees and nakshatras.
- **Sun & Moon Conjunction Finder** – special search for combinations that always include the Sun and Moon plus any number of additional planets.
- **D1 (Lagna) Birth Chart** – enter birth details to generate a whole-sign chart with planetary degrees, nakshatras and house distribution. The tool tries to detect the correct time zone from the location but lets you override it.
- **Transit Explorer** – view planetary sign changes for any year with an optional planet filter and month range.
- **Colorful CLI** – progress bars, tables and panels are rendered with the Rich library for easy reading.
- **Vedic/Tropical Modes** – select sidereal or tropical calculations when starting the program.
- **New & Full Moon Finder** – list exact times and signs of each lunation within a chosen date range.

## Requirements
- Python 3.8 or later
- Packages: `rich`, `skyfield`, `swisseph`, `geopy`, `pytz`, `timezonefinder`
- Swiss Ephemeris `.se1` files and the `de440.bsp` planetary ephemeris in this directory

## Usage
1. Install the dependencies:
   ```bash
   pip install rich skyfield swisseph geopy pytz timezonefinder
   ```
2. Run the menu-driven program:
   ```bash
   python DracoVed_v1.py
   ```
3. Choose an option from the menu to search for conjunctions, check transits or generate a chart.

## Project Layout
- `DracoVed_v1.py` – main entry point providing the interactive menu
- `features.py` – implementations for conjunction searches, transits and chart generation
- `astro_utils.py` – astronomical helper functions
- `display_utils.py` – utilities for Rich output
- `config.py` – global constants and settings

## Notes
- Ensure the required ephemeris files are present alongside the scripts.
- Unicode and ANSI-color capable terminals provide the best display.

---
Created by Mahir, 2025.
