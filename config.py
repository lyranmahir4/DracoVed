# Configuration, constants, and lists for DracoVed
import os
import swisseph as swe

# --- Configuration ---
EPHEMERIS_SKYFIELD = 'de440.bsp'
SCRIPT_DIRECTORY = os.path.dirname(os.path.abspath(__file__))
EPHEMERIS_PATH_SWISSEPH = SCRIPT_DIRECTORY # .se1 files MUST be here

# Calculation mode: 'sidereal' for Vedic, 'tropical' for Western
MODE = 'sidereal'

PLANET_SKYFIELD_NAMES = {
    "Sun": 'sun',
    "Moon": 'moon',
    "Mercury": 'mercury',
    "Venus": 'venus',
    "Mars": 'mars barycenter',
    "Jupiter": 'jupiter barycenter',
    "Saturn": 'saturn barycenter'
}

ZODIAC_SIGNS_SIDEREAL = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
]

ALL_PLANETS = [
    "Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Rahu", "Ketu"
]

# --- AYANAMSA CHANGE HERE ---
AYANAMSA_SWISSEPH = swe.SIDM_TRUE_CITRA # Changed to True Chitrapaksha
# AYANAMSA_SWISSEPH = swe.SIDM_LAHIRI # This was the previous default

MIN_CONJUNCTING_PLANETS = 4
START_YEAR = 2017
END_YEAR = 2050

NAKSHATRAS = [
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashirsha", "Ardra", "Punarvasu", "Pushya", "Ashlesha",
    "Magha", "Purva Phalguni", "Uttara Phalguni", "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha",
    "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishta", "Shatabhisha", "Purva Bhadrapada", "Uttara Bhadrapada", "Revati"
]
