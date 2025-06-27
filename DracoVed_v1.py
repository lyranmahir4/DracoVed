# DracoVed main script (entry point)
import config
from config import *
from astro_utils import *
from display_utils import console, print_rich_table
from features import find_conjunctions, find_pair_conjunctions, print_d1_birth_chart
from skyfield.api import load
import swisseph as swe
from datetime import datetime
from rich.text import Text

# --- Skyfield Setup ---
ts = load.timescale()
eph = load(EPHEMERIS_SKYFIELD)
earth = eph['earth']
# --- pyswisseph Setup ---
swe.set_ephe_path(EPHEMERIS_PATH_SWISSEPH)
swe.set_sid_mode(AYANAMSA_SWISSEPH)

if __name__ == "__main__":
    title = Text("DracoVed", style="bold cyan")
    console.print("\n" + "." * 20, title, "." * 20)
    console.print("[bold yellow]Select calculation mode:[/bold yellow]")
    console.print("  1. Vedic (sidereal)")
    console.print("  2. Tropical (western)")
    mode_in = input("Enter 1 or 2 [1]: ").strip()
    if mode_in == "2":
        config.MODE = 'tropical'
        swe.set_sid_mode(swe.SIDM_NONE)
        console.print("[green]Tropical mode selected.[/green]")
    else:
        config.MODE = 'sidereal'
        swe.set_sid_mode(AYANAMSA_SWISSEPH)
        console.print("[green]Vedic (sidereal) mode selected.[/green]")
    while True:
        console.print("\n[bold yellow]Please select an option:[/bold yellow]")
        console.print("  1. Find all dates with N-planet conjunctions")
        console.print("  2. Find all dates when two specific planets conjunct")
        console.print("  3. Show D1 birth chart details")
        console.print("  4. Show planetary transits")
        console.print("  5. Find conjunctions with Sun+Moon + N planets")
        console.print("  6. List New and Full Moons")
        console.print("  0. Exit")
        choice = input("Enter your choice (0/1/2/3/4/5/6): ").strip()
        if choice == "0":
            console.print("[bold green]Goodbye![/bold green]")
            break
        elif choice == "1":
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
            find_conjunctions(start_dt_obj, end_dt_obj, n_planets, eph, earth, ts)
        elif choice == "2":
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
            find_pair_conjunctions(start_dt_obj, end_dt_obj, planet1, planet2, eph, earth, ts)
        elif choice == "3":
            print_d1_birth_chart(eph, earth, ts)
        elif choice == "4":
            from features import show_transits
            show_transits(eph, earth, ts)
        elif choice == "5":
            while True:
                try:
                    n_planets = int(input(f"Enter total number of planets for conjunction (min 3): ").strip())
                    if n_planets >= 3:
                        break
                    else:
                        console.print("[red]Please enter a number 3 or greater.[/red]")
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
            from features import find_conjunctions_with_sun_moon
            find_conjunctions_with_sun_moon(start_dt_obj, end_dt_obj, n_planets, eph, earth, ts)
        elif choice == "6":
            while True:
                try:
                    start_str = input("Enter start date (YYYY-MM-DD): ").strip()
                    end_str = input("Enter end date   (YYYY-MM-DD): ").strip()
                    start_dt_obj = datetime.strptime(start_str, "%Y-%m-%d")
                    end_dt_obj = datetime.strptime(end_str, "%Y-%m-%d")
                    if start_dt_obj <= end_dt_obj:
                        break
                    else:
                        console.print("[red]Start date must be before end date.[/red]")
                except Exception:
                    console.print("[red]Invalid date format. Please use YYYY-MM-DD.[/red]")
            from features import list_new_full_moons
            list_new_full_moons(start_dt_obj, end_dt_obj, eph, earth, ts)
        else:
            console.print("[red]Invalid choice. Please enter 0, 1, 2, 3, 4, 5, or 6.[/red]")
