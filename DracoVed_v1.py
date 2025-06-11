from skyfield.api import load, Topos
from skyfield.framelib import ecliptic_frame
from datetime import datetime, timedelta, timezone
from collections import defaultdict
import swisseph as swe
import os
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, BarColumn, TextColumn, TimeElapsedColumn, TimeRemainingColumn
from rich.panel import Panel
from rich.text import Text
from geopy.geocoders import Nominatim

# Initialize rich console
console = Console()

# --- Configuration ---
EPHEMERIS_SKYFIELD = 'de440.bsp'
SCRIPT_DIRECTORY = os.path.dirname(os.path.abspath(__file__))
EPHEMERIS_PATH_SWISSEPH = SCRIPT_DIRECTORY # .se1 files MUST be here

PLANET_SKYFIELD_NAMES = {
    "Sun": 'sun',
    "Moon": 'moon',
    "Mercury": 'mercury',
    "Venus": 'venus',
    "Mars": 'mars',
    "Jupiter": 'jupiter barycenter',
    "Saturn": 'saturn barycenter'
}

ZODIAC_SIGNS_SIDEREAL = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
]

# Add Rahu and Ketu to the planet list for user options
ALL_PLANETS = [
    "Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Rahu", "Ketu"
]

# --- AYANAMSA CHANGE HERE ---
AYANAMSA_SWISSEPH = swe.SIDM_TRUE_CITRA # Changed to True Chitrapaksha
# AYANAMSA_SWISSEPH = swe.SIDM_LAHIRI # This was the previous default

MIN_CONJUNCTING_PLANETS = 4
START_YEAR = 2017
END_YEAR = 2050
# --- End Configuration ---

# --- Skyfield Setup ---
ts = load.timescale()
eph = load(EPHEMERIS_SKYFIELD)
earth = eph['earth']
# --- End Skyfield Setup ---

# --- pyswisseph Setup (for Ayanamsha & Rahu) ---
# This path needs to contain the .se1 files for pyswisseph
swe.set_ephe_path(EPHEMERIS_PATH_SWISSEPH)
swe.set_sid_mode(AYANAMSA_SWISSEPH) # This sets the chosen Ayanamsha for swe.get_ayanamsa_ut
# --- End pyswisseph Setup ---

def get_skyfield_time(year, month, day, hour=12, minute=0, second=0): # Noon UTC for daily check
    dt_utc = datetime(year, month, day, hour, minute, second, tzinfo=timezone.utc)
    return ts.utc(dt_utc)

def get_julian_day_from_skyfield_time(t_skyfield):
    return t_skyfield.ut1

def get_ayanamsa_value(jd_ut):
    try:
        # swe.get_ayanamsa_ut uses the Ayanamsha set by swe.set_sid_mode()
        val = swe.get_ayanamsa_ut(jd_ut)
        return val
    except Exception:
        return None

def get_tropical_ecliptic_longitude_skyfield(t_skyfield, planet_name_skyfield):
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
        # swe.TRUE_NODE for Rahu
        # flags = 0 for tropical longitude (default for calc_ut if FLG_SIDEREAL is not set)
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

def print_rich_table(headers, rows, title=None):
    table = Table(title=title, show_lines=True, header_style="bold magenta")
    for h in headers:
        table.add_column(h, style="bold cyan")
    for row in rows:
        table.add_row(*[str(x) for x in row])
    console.print(table)

def find_conjunctions(start_date_dt, end_date_dt, min_planets):
    ayanamsa_name_str = "True Chitrapaksha" if AYANAMSA_SWISSEPH == swe.SIDM_TRUE_CITRA else \
                        "Lahiri" if AYANAMSA_SWISSEPH == swe.SIDM_LAHIRI else \
                        f"Custom ({AYANAMSA_SWISSEPH})"
    total_days = (end_date_dt - start_date_dt).days + 1
    config_table = [
        ["Time Range", f"{start_date_dt.strftime('%Y-%m-%d')} to {end_date_dt.strftime('%Y-%m-%d')}"],
        ["Ephemeris", "Skyfield (Sun-Saturn), pyswisseph (Rahu)"],
        ["Ayanamsha", ayanamsa_name_str],
        ["SE1 Path", EPHEMERIS_PATH_SWISSEPH],
        ["Min Planets", str(min_planets)]
    ]
    console.print(Panel.fit("[bold magenta]Vedic Conjunction Search Parameters[/bold magenta]", style="cyan"))
    print_rich_table(["Parameter", "Value"], config_table)
    current_date = start_date_dt
    found_conjunctions = {}
    pyswisseph_functional_for_ayanamsa = True
    pyswisseph_functional_for_rahu = True
    t_sky_initial_check = get_skyfield_time(current_date.year, current_date.month, current_date.day)
    jd_ut_initial_check = get_julian_day_from_skyfield_time(t_sky_initial_check)
    initial_ayanamsa = get_ayanamsa_value(jd_ut_initial_check)
    if initial_ayanamsa is None:
        console.print("[bold red]CRITICAL PYSWISSEPH ERROR: Cannot calculate Ayanamsha.")
        console.print(f"Please ensure Swiss Ephemeris .se1 files are in the script directory: {EPHEMERIS_PATH_SWISSEPH}")
        console.print("Aborting search as sidereal calculations are not possible.")
        return
    initial_rahu = get_rahu_tropical_longitude_swisseph(jd_ut_initial_check)
    if initial_rahu is None:
        console.print("[yellow]PYSWISSEPH WARNING: Cannot calculate Rahu's position initially.")
        console.print(f"Ensure Swiss Ephemeris .se1 files (for nodes) are in: {EPHEMERIS_PATH_SWISSEPH}")
        console.print("Continuing search, but Rahu will be excluded if this persists.")
        pyswisseph_functional_for_rahu = False
    found_conjunctions_list = []
    with Progress(
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("{task.completed}/{task.total}"),
        TimeElapsedColumn(),
        TimeRemainingColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("Calculating", total=total_days)
        while current_date <= end_date_dt:
            t_sky = get_skyfield_time(current_date.year, current_date.month, current_date.day)
            jd_ut = get_julian_day_from_skyfield_time(t_sky)
            ayanamsa = None
            if pyswisseph_functional_for_ayanamsa:
                ayanamsa = get_ayanamsa_value(jd_ut)
                if ayanamsa is None:
                    pyswisseph_functional_for_ayanamsa = False
            planet_positions_in_signs = defaultdict(list)
            planet_degrees = {}
            if pyswisseph_functional_for_ayanamsa:
                for display_name, skyfield_name in PLANET_SKYFIELD_NAMES.items():
                    tropical_lon = get_tropical_ecliptic_longitude_skyfield(t_sky, skyfield_name)
                    if tropical_lon is not None:
                        sidereal_lon = get_sidereal_longitude(tropical_lon, ayanamsa)
                        if sidereal_lon is not None:
                            sign_index = get_zodiac_sign_index(sidereal_lon)
                            if sign_index is not None:
                                planet_positions_in_signs[sign_index].append(display_name)
                                planet_degrees[display_name] = sidereal_lon
                # Rahu
                if pyswisseph_functional_for_rahu:
                    rahu_tropical_lon = get_rahu_tropical_longitude_swisseph(jd_ut)
                    if rahu_tropical_lon is not None:
                        rahu_sidereal_lon = get_sidereal_longitude(rahu_tropical_lon, ayanamsa)
                        if rahu_sidereal_lon is not None:
                            rahu_sign_index = get_zodiac_sign_index(rahu_sidereal_lon)
                            if rahu_sign_index is not None:
                                planet_positions_in_signs[rahu_sign_index].append("Rahu")
                                planet_degrees["Rahu"] = rahu_sidereal_lon
                # Ketu
                if pyswisseph_functional_for_rahu:
                    rahu_tropical_lon = get_rahu_tropical_longitude_swisseph(jd_ut)
                    if rahu_tropical_lon is not None:
                        ketu_tropical_lon = (rahu_tropical_lon + 180.0) % 360.0
                        ketu_sidereal_lon = get_sidereal_longitude(ketu_tropical_lon, ayanamsa)
                        if ketu_sidereal_lon is not None:
                            ketu_sign_index = get_zodiac_sign_index(ketu_sidereal_lon)
                            if ketu_sign_index is not None:
                                planet_positions_in_signs[ketu_sign_index].append("Ketu")
                                planet_degrees["Ketu"] = ketu_sidereal_lon
            for sign_index, planets_in_sign in planet_positions_in_signs.items():
                if len(planets_in_sign) >= min_planets:
                    sign_name = ZODIAC_SIGNS_SIDEREAL[sign_index]
                    # Detailed degrees and nakshatra for each planet
                    details = []
                    for p in sorted(planets_in_sign):
                        deg = planet_degrees.get(p, None)
                        deg_str = format_degree_in_sign(deg)
                        nak, pada = get_nakshatra_and_pada(deg)
                        # Color planet name for clarity
                        details.append(f"[bold yellow]{p}[/bold yellow] ([cyan]{deg_str}°[/cyan] {nak}-{pada})")
                    planets_str = "\n".join(details)
                    conjunction_key = (sign_name, tuple(sorted(planets_in_sign)))
                    if conjunction_key not in found_conjunctions or \
                       found_conjunctions[conjunction_key] != current_date - timedelta(days=1):
                        ayanamsa_str = f"{ayanamsa:.4f}" if ayanamsa is not None else "N/A"
                        found_conjunctions_list.append([
                            current_date.strftime('%Y-%m-%d'),
                            sign_name,
                            ayanamsa_str,
                            len(planets_in_sign),
                            planets_str
                        ])
                    found_conjunctions[conjunction_key] = current_date
            if not pyswisseph_functional_for_ayanamsa:
                console.print("[bold red]Halting search as Ayanamsha calculation is no longer functional (pyswisseph issue).")
                return
            current_date += timedelta(days=1)
            progress.update(task, advance=1)
    if found_conjunctions_list:
        console.print(Panel.fit("[bold green]═══ CONJUNCTION SEARCH RESULTS ═══[/bold green]", style="green"))
        print_rich_table(["Date", "Sign", "Ayanamsha", "# Planets", "Planets (Deg, Nakshatra-Pada)"], found_conjunctions_list)
    else:
        console.print("[yellow]No conjunctions found meeting the criteria.")
    console.print("[bold green]Search complete.[/bold green]")


def find_pair_conjunctions(start_date_dt, end_date_dt, planet1, planet2):
    console.print(Panel.fit(f"[bold cyan]Searching for conjunctions between {planet1} and {planet2} from {start_date_dt.year} to {end_date_dt.year}[/bold cyan]", style="cyan"))
    total_days = (end_date_dt - start_date_dt).days + 1
    conjunction_dates = []
    current_date = start_date_dt
    with Progress(
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("{task.completed}/{task.total}"),
        TimeElapsedColumn(),
        TimeRemainingColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("Calculating", total=total_days)
        while current_date <= end_date_dt:
            t_sky = get_skyfield_time(current_date.year, current_date.month, current_date.day)
            jd_ut = get_julian_day_from_skyfield_time(t_sky)
            ayanamsa = get_ayanamsa_value(jd_ut)
            positions = {}
            nakshatras = {}
            # Get sidereal longitude and nakshatra for each planet
            for p in [planet1, planet2]:
                if p in PLANET_SKYFIELD_NAMES:
                    tropical_lon = get_tropical_ecliptic_longitude_skyfield(t_sky, PLANET_SKYFIELD_NAMES[p])
                elif p == "Rahu":
                    tropical_lon = get_rahu_tropical_longitude_swisseph(jd_ut)
                elif p == "Ketu":
                    rahu_lon = get_rahu_tropical_longitude_swisseph(jd_ut)
                    tropical_lon = (rahu_lon + 180.0) % 360.0 if rahu_lon is not None else None
                else:
                    tropical_lon = None
                if tropical_lon is not None and ayanamsa is not None:
                    sidereal = get_sidereal_longitude(tropical_lon, ayanamsa)
                    positions[p] = sidereal
                    nakshatras[p] = get_nakshatra_and_pada(sidereal)
                else:
                    positions[p] = None
                    nakshatras[p] = ("N/A", "N/A")
            # Check if both planets are in the same sign
            if positions[planet1] is not None and positions[planet2] is not None:
                sign1 = get_zodiac_sign_index(positions[planet1])
                sign2 = get_zodiac_sign_index(positions[planet2])
                if sign1 == sign2:
                    deg1 = format_degree_in_sign(positions[planet1])
                    deg2 = format_degree_in_sign(positions[planet2])
                    n1, p1 = nakshatras[planet1]
                    n2, p2 = nakshatras[planet2]
                    conjunction_dates.append([
                        current_date.strftime('%Y-%m-%d'),
                        ZODIAC_SIGNS_SIDEREAL[sign1],
                        f"[bold yellow]{planet1}[/bold yellow] ([cyan]{deg1}°[/cyan] {n1}-{p1})",
                        f"[bold yellow]{planet2}[/bold yellow] ([cyan]{deg2}°[/cyan] {n2}-{p2})"
                    ])
            current_date += timedelta(days=1)
            progress.update(task, advance=1)
    if conjunction_dates:
        console.print(Panel.fit("[bold green]Conjunctions found:[/bold green]", style="green"))
        print_rich_table(["Date", "Sign", f"{planet1} (Deg, Nakshatra-Pada)", f"{planet2} (Deg, Nakshatra-Pada)"], conjunction_dates)
    else:
        console.print(f"[yellow]No conjunctions found for {planet1} and {planet2} in the given range.")

# Nakshatra calculation
NAKSHATRAS = [
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashirsha", "Ardra", "Punarvasu", "Pushya", "Ashlesha",
    "Magha", "Purva Phalguni", "Uttara Phalguni", "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha",
    "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishta", "Shatabhisha", "Purva Bhadrapada", "Uttara Bhadrapada", "Revati"
]

# Helper to get Nakshatra name and pada
def get_nakshatra_and_pada(sidereal_long):
    if sidereal_long is None:
        return ("N/A", "N/A")
    nak_num = int(sidereal_long // (360/27))
    pada_num = int((sidereal_long % (360/27)) // (360/27/4)) + 1
    return (NAKSHATRAS[nak_num], pada_num)

def get_location_coordinates():
    console.print("[bold yellow]Enter birth place (city/town/village or coordinates):[/bold yellow]")
    place = input("Place name (or leave blank to enter lat/lon manually): ").strip()
    if place:
        geolocator = Nominatim(user_agent="astro_d1_chart")
        try:
            location = geolocator.geocode(place, timeout=10)
            if location:
                console.print(f"[green]Found:[/green] {location.address} (lat: {location.latitude:.4f}, lon: {location.longitude:.4f})")
                return location.latitude, location.longitude
            else:
                console.print("[red]Could not find location. Please enter latitude and longitude manually.[/red]")
        except Exception as e:
            console.print(f"[red]Geocoding error: {e}. Please enter latitude and longitude manually.[/red]")
    # Manual entry fallback
    while True:
        try:
            lat = float(input("Latitude (e.g. 28.6139): ").strip())
            lon = float(input("Longitude (e.g. 77.2090): ").strip())
            return lat, lon
        except ValueError:
            console.print("[red]Invalid input. Please enter valid numbers for latitude and longitude.[/red]")

def print_d1_birth_chart():
    console.print("[bold yellow]Enter birth details for D1 chart:[/bold yellow]")
    name = input("Name (optional): ").strip()
    year = int(input("Year (e.g. 1990): ").strip())
    month = int(input("Month (1-12): ").strip())
    day = int(input("Day (1-31): ").strip())
    hour = int(input("Hour (0-23): ").strip())
    minute = int(input("Minute (0-59): ").strip())
    second = int(input("Second (0-59, default 0): ") or "0")
    lat, lon = get_location_coordinates()
    dt_utc = datetime(year, month, day, hour, minute, int(second), tzinfo=timezone.utc)
    t_sky = ts.utc(dt_utc)
    jd_ut = get_julian_day_from_skyfield_time(t_sky)
    ayanamsa = get_ayanamsa_value(jd_ut)
    if ayanamsa is None:
        console.print("[bold red]Error: Unable to compute Ayanamsa. Chart cannot be generated.[/bold red]")
        return
    # Ascendant calculation (robust, Skyfield way)
    from skyfield.api import wgs84
    observer = wgs84.latlon(lat, lon)
    asc_icrf = observer.at(t_sky).from_altaz(alt_degrees=0, az_degrees=90)
    asc_ecl_lat, asc_ecl_lon, _ = asc_icrf.ecliptic_latlon()
    asc_long = asc_ecl_lon.degrees
    asc_sid_long = get_sidereal_longitude(asc_long, ayanamsa)
    asc_sign_index = get_zodiac_sign_index(asc_sid_long)
    asc_sign = ZODIAC_SIGNS_SIDEREAL[asc_sign_index] if asc_sign_index is not None else "N/A"
    asc_deg_in_sign = format_degree_in_sign(asc_sid_long)
    asc_nak, asc_pada = get_nakshatra_and_pada(asc_sid_long)
    # Planets
    planet_rows = []
    planet_positions = {}
    for planet in ALL_PLANETS:
        try:
            if planet in PLANET_SKYFIELD_NAMES:
                tropical_lon = get_tropical_ecliptic_longitude_skyfield(t_sky, PLANET_SKYFIELD_NAMES[planet])
            elif planet == "Rahu":
                tropical_lon = get_rahu_tropical_longitude_swisseph(jd_ut)
            elif planet == "Ketu":
                rahu_lon = get_rahu_tropical_longitude_swisseph(jd_ut)
                tropical_lon = (rahu_lon + 180.0) % 360.0 if rahu_lon is not None else None
            else:
                tropical_lon = None
            if tropical_lon is None:
                console.print(f"[red]Warning: Could not calculate position for {planet}[/red]")
                continue
            sidereal_lon = get_sidereal_longitude(tropical_lon, ayanamsa)
            if sidereal_lon is None:
                console.print(f"[red]Warning: Could not calculate sidereal position for {planet}[/red]")
                continue
            sign_index = get_zodiac_sign_index(sidereal_lon)
            sign_name = ZODIAC_SIGNS_SIDEREAL[sign_index] if sign_index is not None else "N/A"
            deg_in_sign = format_degree_in_sign(sidereal_lon)
            nak, pada = get_nakshatra_and_pada(sidereal_lon)
            planet_positions[planet] = sidereal_lon
            planet_rows.append([
                f"[bold yellow]{planet}[/bold yellow]",
                f"[cyan]{deg_in_sign}°[/cyan]",
                sign_name,
                f"{nak}-{pada}"
            ])
        except Exception as e:
            console.print(f"[red]Error calculating {planet}'s position: {str(e)}[/red]")
    # House calculation: 30° per house from ascendant (using exact degree, not sign)
    def get_house_number(planet_longitude, asc_longitude):
        rel_angle = (planet_longitude - asc_longitude + 360) % 360
        house = 1 + int(rel_angle // 30)
        return house
    house_planets = {i+1: [] for i in range(12)}
    for planet, sid_long in planet_positions.items():
        if sid_long is None:
            continue
        house = get_house_number(sid_long, asc_sid_long)
        house_planets[house].append(planet)
    # Print chart
    title = f"[bold magenta]D1 Birth Chart for {name if name else 'Person'}[/bold magenta]"
    chart_table = Table(title=title, show_lines=True)
    chart_table.add_column("Planet", style="bold yellow")
    chart_table.add_column("Deg in Sign", style="cyan")
    chart_table.add_column("Sign", style="bold cyan")
    chart_table.add_column("Nakshatra-Pada")
    for row in planet_rows:
        chart_table.add_row(*row)
    console.print(Panel.fit(f"[bold green]Ascendant: {asc_sign} {asc_deg_in_sign}° ({asc_nak}-{asc_pada})[/bold green]", style="green"))
    console.print(chart_table)
    # Print house-wise planets
    house_table = Table(title="[bold magenta]Planets in Houses (from Ascendant)[/bold magenta]", show_lines=True)
    house_table.add_column("House", style="bold yellow")
    house_table.add_column("Planets", style="bold cyan")
    for i in range(1, 13):
        plist = ", ".join(house_planets[i]) if house_planets[i] else "-"
        house_table.add_row(str(i), plist)
    console.print(house_table)

if __name__ == "__main__":
    title = Text("Vedic Conjunction Finder", style="bold cyan")
    console.print("\n" + "." * 20, title, "." * 20)
    while True:
        console.print("\n[bold yellow]Please select an option:[/bold yellow]")
        console.print("  1. Find all dates with N-planet conjunctions")
        console.print("  2. Find all dates when two specific planets conjunct")
        console.print("  3. Show D1 birth chart details")
        console.print("  0. Exit")
        choice = input("Enter your choice (0/1/2/3): ").strip()
        if choice == "0":
            console.print("[bold green]Goodbye![/bold green]")
            break
        elif choice == "1":
            # Option 1: N-planet conjunctions
            while True:
                try:
                    n_planets = int(input(f"Enter number of planets for conjunction (2-7): ").strip())
                    if 2 <= n_planets <= 7:
                        break
                    else:
                        console.print("[red]Please enter a number between 2 and 7.[/red]")
                except ValueError:
                    console.print("[red]Invalid input. Please enter a number.[/red]")
            while True:
                try:
                    start_year = int(input(f"Enter start year (e.g. 2017): ").strip())
                    end_year = int(input(f"Enter end year (e.g. 2050): ").strip())
                    if start_year <= end_year:
                        break
                    else:
                        console.print("[red]Start year must be less than or equal to end year.[/red]")
                except ValueError:
                    console.print("[red]Invalid input. Please enter a valid year.[/red]")
            start_dt_obj = datetime(start_year, 1, 1)
            end_dt_obj = datetime(end_year, 12, 31)
            find_conjunctions(start_dt_obj, end_dt_obj, n_planets)
        elif choice == "2":
            # Option 2: Specific pair
            console.print(f"Available planets: {', '.join(ALL_PLANETS)}")
            while True:
                planet1 = input(f"Enter first planet: ").strip().capitalize()
                if planet1 in ALL_PLANETS:
                    break
                else:
                    console.print("[red]Invalid planet name. Try again.[/red]")
            while True:
                planet2 = input(f"Enter second planet: ").strip().capitalize()
                if planet2 in ALL_PLANETS and planet2 != planet1:
                    break
                else:
                    console.print("[red]Invalid or duplicate planet name. Try again.[/red]")
            while True:
                try:
                    start_year = int(input(f"Enter start year (e.g. 2017): ").strip())
                    end_year = int(input(f"Enter end year (e.g. 2050): ").strip())
                    if start_year <= end_year:
                        break
                    else:
                        console.print("[red]Start year must be less than or equal to end year.[/red]")
                except ValueError:
                    console.print("[red]Invalid input. Please enter a valid year.[/red]")
            start_dt_obj = datetime(start_year, 1, 1)
            end_dt_obj = datetime(end_year, 12, 31)
            find_pair_conjunctions(start_dt_obj, end_dt_obj, planet1, planet2)
        elif choice == "3":
            print_d1_birth_chart()
        else:
            console.print("[red]Invalid choice. Please enter 0, 1, 2, or 3.[/red]")
