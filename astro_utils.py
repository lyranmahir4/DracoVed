# Astronomy and calculation utilities for DracoVed
from datetime import datetime, timezone
from skyfield.api import load
import swisseph as swe
from config import PLANET_SKYFIELD_NAMES, AYANAMSA_SWISSEPH, ZODIAC_SIGNS_SIDEREAL, NAKSHATRAS

# --- Skyfield Setup ---
ts = load.timescale()
# eph = load(EPHEMERIS_SKYFIELD) # Loaded in main script for path reasons
# earth = eph['earth']

# --- pyswisseph Setup (for Ayanamsha & Rahu) ---
# swe.set_ephe_path(EPHEMERIS_PATH_SWISSEPH) # Set in main script
# swe.set_sid_mode(AYANAMSA_SWISSEPH) # Set in main script

def get_skyfield_time(year, month, day, hour=12, minute=0, second=0):
    dt_utc = datetime(year, month, day, hour, minute, second, tzinfo=timezone.utc)
    return ts.utc(dt_utc)

def get_julian_day_from_skyfield_time(t_skyfield):
    return t_skyfield.ut1

def get_ayanamsa_value(jd_ut):
    try:
        val = swe.get_ayanamsa_ut(jd_ut)
        return val
    except Exception:
        return None

def get_tropical_ecliptic_longitude_skyfield(t_skyfield, planet_name_skyfield, eph, earth):
    if planet_name_skyfield in eph:
        try:
            planet_body = eph[planet_name_skyfield]
            astrometric = earth.at(t_skyfield).observe(planet_body)
            eclat, eclon, _ = astrometric.ecliptic_latlon(epoch='date')
            return eclon.degrees
        except Exception:
            return None
    return None

def get_rahu_tropical_longitude_swisseph(jd_ut):
    try:
        rahu_data, ret_flag = swe.calc_ut(jd_ut, swe.TRUE_NODE, 0)
        if ret_flag < 0:
            return None
        return rahu_data[0]
    except Exception:
        return None

def get_sidereal_longitude(tropical_longitude_deg, ayanamsa_deg):
    if tropical_longitude_deg is None or ayanamsa_deg is None:
        return None
    sidereal_long = (tropical_longitude_deg - ayanamsa_deg + 360.0) % 360.0
    return sidereal_long

def get_zodiac_sign_index(longitude_deg):
    if longitude_deg is None:
        return None
    return int(longitude_deg // 30)

def format_degree_in_sign(sidereal_long):
    if sidereal_long is None:
        return "N/A"
    deg_in_sign = sidereal_long % 30
    return f"{deg_in_sign:05.2f}"

def get_nakshatra_and_pada(sidereal_long):
    if sidereal_long is None:
        return ("N/A", "N/A")
    nak_num = int(sidereal_long // (360/27))
    pada_num = int((sidereal_long % (360/27)) // (360/27/4)) + 1
    return (NAKSHATRAS[nak_num], pada_num)
