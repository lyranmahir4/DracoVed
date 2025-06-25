# Main features for DracoVed: conjunctions and D1 chart
from datetime import datetime, timedelta, timezone
from collections import defaultdict
from rich.progress import Progress, BarColumn, TextColumn, TimeElapsedColumn, TimeRemainingColumn
from rich.panel import Panel
from rich.text import Text
from geopy.geocoders import Nominatim
from config import PLANET_SKYFIELD_NAMES, ZODIAC_SIGNS_SIDEREAL, ALL_PLANETS, AYANAMSA_SWISSEPH, NAKSHATRAS, EPHEMERIS_PATH_SWISSEPH
from display_utils import console, print_rich_table
from astro_utils import *
import swisseph as swe
from rich.table import Table

# The following functions require eph, earth, ts to be passed in from main

def find_conjunctions(start_date_dt, end_date_dt, min_planets, eph, earth, ts):
    ayanamsa_name_str = "True Chitrapaksha" if AYANAMSA_SWISSEPH == swe.SIDM_TRUE_CITRA else \
                        "Lahiri" if AYANAMSA_SWISSEPH == swe.SIDM_LAHIRI else \
                        f"Custom ({AYANAMSA_SWISSEPH})"
    total_days = (end_date_dt - start_date_dt).days + 1
    config_table = [
        ["Time Range", f"{start_date_dt.strftime('%Y-%m-%d')} to {end_date_dt.strftime('%Y-%m-%d')}`"],
        ["Ephemeris", "Skyfield (Sun-Saturn), pyswisseph (Rahu)"],
        ["Ayanamsha", ayanamsa_name_str],
        ["SE1 Path", EPHEMERIS_PATH_SWISSEPH],  # Use config value instead of swe.get_ephe_path()
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
        console.print(f"Please ensure Swiss Ephemeris .se1 files are in the script directory: {swe.get_ephe_path()}")
        console.print("Aborting search as sidereal calculations are not possible.")
        return
    initial_rahu = get_rahu_tropical_longitude_swisseph(jd_ut_initial_check)
    if initial_rahu is None:
        console.print("[yellow]PYSWISSEPH WARNING: Cannot calculate Rahu's position initially.")
        console.print(f"Ensure Swiss Ephemeris .se1 files (for nodes) are in: {swe.get_ephe_path()}")
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
                    tropical_lon = get_tropical_ecliptic_longitude_skyfield(t_sky, skyfield_name, eph, earth)
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
                    details = []
                    for p in sorted(planets_in_sign):
                        deg = planet_degrees.get(p, None)
                        deg_str = format_degree_in_sign(deg)
                        nak, pada = get_nakshatra_and_pada(deg)
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


def find_pair_conjunctions(start_date_dt, end_date_dt, planet1, planet2, eph, earth, ts):
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
            for p in [planet1, planet2]:
                if p in PLANET_SKYFIELD_NAMES:
                    tropical_lon = get_tropical_ecliptic_longitude_skyfield(t_sky, PLANET_SKYFIELD_NAMES[p], eph, earth)
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
    while True:
        try:
            lat = float(input("Latitude (e.g. 28.6139): ").strip())
            lon = float(input("Longitude (e.g. 77.2090): ").strip())
            return lat, lon
        except ValueError:
            console.print("[red]Invalid input. Please enter valid numbers for latitude and longitude.[/red]")


def print_d1_birth_chart(eph, earth, ts):
    console.print("[bold yellow]Enter birth details for D1 chart:[/bold yellow]")
    name = input("Name (optional): ").strip()
    while True:
        try:
            year = int(input("Year (e.g. 1990): ").strip())
            month = int(input("Month (1-12): ").strip())
            day = int(input("Day (1-31): ").strip())
            hour = int(input("Hour (0-23, local time): ").strip())
            minute = int(input("Minute (0-59): ").strip())
            second_str = input("Second (0-59, default 0): ") or "0"
            second = int(second_str)
            datetime(year, month, day, hour, minute, second)
            break
        except ValueError as e:
            console.print(f"[red]Invalid date/time input: {e}. Please try again.[/red]")

    lat, lon = get_location_coordinates()

    local_tz = None
    try:
        from timezonefinder import TimezoneFinder
        import pytz
        tf = TimezoneFinder()
        tz_str = tf.timezone_at(lng=lon, lat=lat)
        if tz_str:
            console.print(f"[green]Detected Timezone:[/green] [bold cyan]{tz_str}[/bold cyan]")
            confirm = input("Is this correct? (Y/n): ").strip().lower()
            if confirm == '' or confirm == 'y':
                local_tz = pytz.timezone(tz_str)
            else:
                console.print("Proceeding with manual timezone entry.")
        else:
            raise ValueError("Could not automatically determine timezone.")
    except (ImportError, ModuleNotFoundError):
        console.print("[bold red]Libraries `pytz` and `timezonefinder` not found.[/bold red]")
        console.print("Please install them for automatic timezone detection: [cyan]pip install pytz timezonefinder[/cyan]")
    except Exception as e:
        console.print(f"[yellow]Warning: {e}.[/yellow]")
    if not local_tz:
        while True:
            try:
                console.print("\n[bold]Please enter the timezone manually.[/bold]")
                console.print("Examples: [cyan]Asia/Dhaka[/cyan], [cyan]America/New_York[/cyan], or a UTC offset like [cyan]+5.5[/cyan] or [cyan]-7[/cyan].")
                tz_input = input("Enter timezone or UTC offset: ").strip()
                try:
                    offset_hours = float(tz_input)
                    offset_minutes = int(offset_hours * 60)
                    local_tz = timezone(timedelta(minutes=offset_minutes))
                    break
                except ValueError:
                    import pytz
                    local_tz = pytz.timezone(tz_input)
                    break
            except Exception as e:
                console.print(f"[red]Invalid timezone or offset: {e}. Please try again.[/red]")
    local_dt = datetime(year, month, day, hour, minute, second)
    aware_local_dt = local_tz.localize(local_dt, is_dst=None)
    dt_utc = aware_local_dt.astimezone(timezone.utc)
    console.print(f"Birth Time (Local): {aware_local_dt.strftime('%Y-%m-%d %H:%M:%S %Z%z')}")
    console.print(f"Birth Time (UTC):   {dt_utc.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    t_sky = ts.from_datetime(dt_utc)
    jd_ut = get_julian_day_from_skyfield_time(t_sky)
    ayanamsa = get_ayanamsa_value(jd_ut)
    if ayanamsa is None:
        console.print("[bold red]Error: Unable to compute Ayanamsa. Chart cannot be generated.[/bold red]")
        return
    cusps, ascmc = swe.houses(jd_ut, lat, lon, b'A')
    asc_long_tropical = ascmc[0]
    asc_sid_long = get_sidereal_longitude(asc_long_tropical, ayanamsa)
    asc_sign_index = get_zodiac_sign_index(asc_sid_long)
    asc_sign = ZODIAC_SIGNS_SIDEREAL[asc_sign_index] if asc_sign_index is not None else "N/A"
    asc_deg_in_sign = format_degree_in_sign(asc_sid_long)
    asc_nak, asc_pada = get_nakshatra_and_pada(asc_sid_long)
    planet_rows = []
    planet_positions = {}
    for planet in ALL_PLANETS:
        try:
            tropical_lon = None
            if planet in PLANET_SKYFIELD_NAMES:
                tropical_lon = get_tropical_ecliptic_longitude_skyfield(t_sky, PLANET_SKYFIELD_NAMES[planet], eph, earth)
            elif planet == "Rahu":
                tropical_lon = get_rahu_tropical_longitude_swisseph(jd_ut)
            elif planet == "Ketu":
                rahu_lon = get_rahu_tropical_longitude_swisseph(jd_ut)
                tropical_lon = (rahu_lon + 180.0) % 360.0 if rahu_lon is not None else None
            if tropical_lon is None:
                console.print(f"[red]Warning: Could not calculate position for {planet}[/red]")
                continue
            sidereal_lon = get_sidereal_longitude(tropical_lon, ayanamsa)
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
    def get_house_number(planet_sign_index, asc_sign_index):
        if planet_sign_index is None or asc_sign_index is None:
            return None
        house = ((planet_sign_index - asc_sign_index + 12) % 12) + 1
        return house
    house_planets = {i + 1: [] for i in range(12)}
    house_planets[1].append("Asc")
    for planet, sid_long in planet_positions.items():
        planet_sign_index = get_zodiac_sign_index(sid_long)
        house = get_house_number(planet_sign_index, asc_sign_index)
        if house is not None:
            house_planets[house].append(planet)
    title = f"[bold magenta]D1 Birth Chart for {name if name else 'Person'}[/bold magenta]"
    chart_table = Table(title=title, show_lines=True)
    chart_table.add_column("Planet", style="bold yellow"); chart_table.add_column("Deg in Sign", style="cyan"); chart_table.add_column("Sign", style="bold cyan"); chart_table.add_column("Nakshatra-Pada")
    for row in planet_rows: chart_table.add_row(*row)
    console.print(Panel.fit(f"[bold green]Ascendant: {asc_sign} {asc_deg_in_sign}° ({asc_nak}-{asc_pada})[/bold green]", style="green"))
    console.print(Panel.fit(f"[bold blue]Ayanamsha (True Chitrapaksha): {ayanamsa:.4f}°[/bold blue]", style="blue"))
    console.print(chart_table)
    house_table = Table(title="[bold magenta]Planets in Houses (Whole Sign System)[/bold magenta]", show_lines=True)
    house_table.add_column("House", style="bold yellow"); house_table.add_column("Sign", style="bold cyan"); house_table.add_column("Planets")
    for i in range(1, 13):
        house_sign_index = (asc_sign_index + i - 1) % 12
        house_sign_name = ZODIAC_SIGNS_SIDEREAL[house_sign_index]
        plist = ", ".join(sorted(house_planets[i])) if house_planets[i] else "-"
        house_table.add_row(str(i), house_sign_name, plist)
    console.print(house_table)


def show_transits(eph, earth, ts):
    console.print("[bold yellow]Show planetary transits[/bold yellow]")
    while True:
        try:
            year = int(input("Enter year (e.g. 2025): ").strip())
            if 1800 <= year <= 2200:
                break
            else:
                console.print("[red]Please enter a valid year between 1800 and 2200.[/red]")
        except ValueError:
            console.print("[red]Invalid input. Please enter a valid year.[/red]")
    # Filter option
    from config import ALL_PLANETS
    console.print(f"Available planets: {', '.join(ALL_PLANETS)}")
    filter_planet = input("Enter a planet name to filter (or press Enter to show all): ").strip().capitalize()
    if filter_planet and filter_planet not in ALL_PLANETS:
        console.print(f"[red]Invalid planet name. Showing all planets.[/red]")
        filter_planet = ""
    mode = "basic"
    console.print("Select mode: [cyan]1. Basic (whole year)[/cyan], [cyan]2. Advanced (select months)[/cyan]")
    mode_choice = input("Enter 1 for basic, 2 for advanced: ").strip()
    if mode_choice == "2":
        mode = "advanced"
    month_start, month_end = 1, 12
    if mode == "advanced":
        while True:
            try:
                month_start = int(input("Enter start month (1-12): ").strip())
                month_end = int(input("Enter end month (1-12): ").strip())
                if 1 <= month_start <= 12 and 1 <= month_end <= 12 and month_start <= month_end:
                    break
                else:
                    console.print("[red]Invalid month range. Try again.[/red]")
            except ValueError:
                console.print("[red]Invalid input. Please enter valid months.[/red]")
    from config import PLANET_SKYFIELD_NAMES, ZODIAC_SIGNS_SIDEREAL
    from astro_utils import get_skyfield_time, get_julian_day_from_skyfield_time, get_ayanamsa_value, get_tropical_ecliptic_longitude_skyfield, get_rahu_tropical_longitude_swisseph, get_sidereal_longitude, get_zodiac_sign_index
    import swisseph as swe
    events_by_month = {m: [] for m in range(month_start, month_end+1)}
    total_days = sum(31 for m in range(month_start, month_end+1))
    with Progress(
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("{task.completed}/{task.total}"),
        TimeElapsedColumn(),
        TimeRemainingColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("Calculating transits", total=total_days)
        for planet in ALL_PLANETS:
            if filter_planet and planet != filter_planet:
                continue
            prev_sign = None
            for month in range(month_start, month_end+1):
                for day in range(1, 32):
                    try:
                        t_sky = get_skyfield_time(year, month, day)
                    except Exception:
                        continue
                    jd_ut = get_julian_day_from_skyfield_time(t_sky)
                    ayanamsa = get_ayanamsa_value(jd_ut)
                    if planet in PLANET_SKYFIELD_NAMES:
                        tropical_lon = get_tropical_ecliptic_longitude_skyfield(t_sky, PLANET_SKYFIELD_NAMES[planet], eph, earth)
                    elif planet == "Rahu":
                        tropical_lon = get_rahu_tropical_longitude_swisseph(jd_ut)
                    elif planet == "Ketu":
                        rahu_lon = get_rahu_tropical_longitude_swisseph(jd_ut)
                        tropical_lon = (rahu_lon + 180.0) % 360.0 if rahu_lon is not None else None
                    else:
                        tropical_lon = None
                    if tropical_lon is None or ayanamsa is None:
                        progress.update(task, advance=1)
                        continue
                    sidereal_lon = get_sidereal_longitude(tropical_lon, ayanamsa)
                    sign_index = get_zodiac_sign_index(sidereal_lon)
                    if sign_index is None:
                        progress.update(task, advance=1)
                        continue
                    if prev_sign is None:
                        prev_sign = sign_index
                    elif sign_index != prev_sign:
                        events_by_month[month].append([f"{year}-{month:02d}-{day:02d}", planet, ZODIAC_SIGNS_SIDEREAL[sign_index]])
                        prev_sign = sign_index
                    progress.update(task, advance=1)
    any_events = False
    for month in range(month_start, month_end+1):
        month_events = events_by_month[month]
        if month_events:
            any_events = True
            month_name = datetime(year, month, 1).strftime("%B")
            table = Table(title=f"[bold magenta]{month_name} {year}[/bold magenta]", show_lines=True)
            table.add_column("Date", style="cyan")
            table.add_column("Planet", style="bold yellow")
            table.add_column("Sign Entered", style="bold cyan")
            for row in month_events:
                table.add_row(*row)
            console.print(table)
    if not any_events:
        console.print("[yellow]No transits found for the selected period.")
def find_conjunctions_with_sun_moon(start_date_dt, end_date_dt, min_planets, eph, earth, ts):
    ayanamsa_name_str = "True Chitrapaksha" if AYANAMSA_SWISSEPH == swe.SIDM_TRUE_CITRA else \
                        "Lahiri" if AYANAMSA_SWISSEPH == swe.SIDM_LAHIRI else \
                        f"Custom ({AYANAMSA_SWISSEPH})"
    total_days = (end_date_dt - start_date_dt).days + 1
    config_table = [
        ["Time Range", f"{start_date_dt.strftime('%Y-%m-%d')} to {end_date_dt.strftime('%Y-%m-%d')}`"],
        ["Ephemeris", "Skyfield (Sun-Saturn), pyswisseph (Rahu)"],
        ["Ayanamsha", ayanamsa_name_str],
        ["SE1 Path", EPHEMERIS_PATH_SWISSEPH],
        ["Min Planets (with Sun+Moon)", str(min_planets)]
    ]
    console.print(Panel.fit("[bold magenta]Vedic Conjunctions: Sun+Moon + N Planets[/bold magenta]", style="cyan"))
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
                    tropical_lon = get_tropical_ecliptic_longitude_skyfield(t_sky, skyfield_name, eph, earth)
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
                # Only consider conjunctions that include both Sun and Moon
                if "Sun" in planets_in_sign and "Moon" in planets_in_sign and len(planets_in_sign) >= min_planets:
                    sign_name = ZODIAC_SIGNS_SIDEREAL[sign_index]
                    details = []
                    for p in sorted(planets_in_sign):
                        deg = planet_degrees.get(p, None)
                        deg_str = format_degree_in_sign(deg)
                        nak, pada = get_nakshatra_and_pada(deg)
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
        console.print(Panel.fit("[bold green]═══ SUN+MOON+N-PLANET CONJUNCTIONS ═══[/bold green]", style="green"))
        print_rich_table(["Date", "Sign", "Ayanamsha", "# Planets", "Planets (Deg, Nakshatra-Pada)"], found_conjunctions_list)
    else:
        console.print("[yellow]No conjunctions found meeting the criteria.")
    console.print("[bold green]Search complete.[/bold green]")
