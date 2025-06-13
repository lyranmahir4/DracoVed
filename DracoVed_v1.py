# DracoVed main script (entry point)
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
    title = Text("Vedic Conjunction Finder", style="bold cyan")
    console.print("\n" + "." * 20, title, "." * 20)
    while True:
        console.print("\n[bold yellow]Please select an option:[/bold yellow]")
        console.print("  1. Find all dates with N-planet conjunctions")
        console.print("  2. Find all dates when two specific planets conjunct")
        console.print("  3. Show D1 birth chart details")
        console.print("  4. Show planetary transits")
        console.print("  0. Exit")
        choice = input("Enter your choice (0/1/2/3/4): ").strip()
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
        else:
            console.print("[red]Invalid choice. Please enter 0, 1, 2, 3, or 4.[/red]")