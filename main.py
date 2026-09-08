#!/usr/bin/env python3
"""
main.py
-------
Command-line Panchang / birth-details calculator.

Usage (interactive):
    python3 main.py

Usage (non-interactive, all args on the command line):
    python3 main.py --date 1999-04-01 --time 04:00 --place Dhanbad
    python3 main.py --date 2001-10-26 --time 13:30 \
                     --lat 30.39 --lon 78.48 --tz 5.5 --place "Tehri Garhwal"
"""

from __future__ import annotations

import argparse
from datetime import datetime

import places
from panchang import BirthInput, compute_panchang, vimshottari_dasha_sequence


def parse_args():
    p = argparse.ArgumentParser(description="Calculate Vedic Panchang from date, time and place of birth.")
    p.add_argument("--date", help="Birth date, YYYY-MM-DD")
    p.add_argument("--time", help="Birth time, HH:MM (24-hour) or HH:MM:SS")
    p.add_argument("--place", help="Place name (looked up in the built-in city database)")
    p.add_argument("--lat", type=float, help="Latitude (used if --place is unknown or omitted)")
    p.add_argument("--lon", type=float, help="Longitude (used if --place is unknown or omitted)")
    p.add_argument("--tz", type=float, help="UTC offset in hours, e.g. 5.5 for IST")
    p.add_argument("--dasha", action="store_true", help="Also print the Vimshottari Mahadasha sequence")
    return p.parse_args()


def prompt(text: str, default: str | None = None) -> str:
    suffix = f" [{default}]" if default else ""
    val = input(f"{text}{suffix}: ").strip()
    return val if val else (default or "")


def gather_input(args) -> BirthInput:
    date_str = args.date or prompt("Date of birth (YYYY-MM-DD)")
    time_str = args.time or prompt("Time of birth (HH:MM, 24-hour)")

    if ":" in time_str and time_str.count(":") == 1:
        time_str += ":00"
    dt = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M:%S")

    lat, lon, tz = args.lat, args.lon, args.tz
    place_name = args.place or ""

    if lat is None or lon is None or tz is None:
        if not place_name:
            place_name = prompt("Place of birth (city name)")
        found = places.lookup(place_name)
        if found:
            lat, lon, tz = found
            print(f"  -> Found '{place_name}' in database: lat={lat}, lon={lon}, UTC{tz:+.1f}")
        else:
            print(f"  -> '{place_name}' not found in the built-in database.")
            lat = float(prompt("  Enter latitude (e.g. 28.6139)"))
            lon = float(prompt("  Enter longitude (e.g. 77.2090)"))
            tz = float(prompt("  Enter UTC offset in hours (e.g. 5.5 for IST)", "5.5"))

    return BirthInput(
        year=dt.year, month=dt.month, day=dt.day,
        hour=dt.hour, minute=dt.minute, second=dt.second,
        tz_offset_hours=tz, latitude=lat, longitude=lon, place_name=place_name,
    )


def print_report(result, show_dasha: bool):
    inp = result.input
    line = "=" * 56

    print(f"\n{line}")
    print(" PANCHANG REPORT")
    print(line)
    print(f" Date of Birth   : {inp.year:04d}-{inp.month:02d}-{inp.day:02d}")
    print(f" Time of Birth   : {inp.hour:02d}:{inp.minute:02d}:{inp.second:02d} "
          f"(UTC{inp.tz_offset_hours:+.1f})")
    print(f" Place           : {inp.place_name or '(manual coordinates)'}  "
          f"(lat {inp.latitude:.4f}, lon {inp.longitude:.4f})")
    print(line)
    print(f" Vara (Weekday)  : {result.vara_name}")
    print(f" Tithi           : {result.tithi_name}  "
          f"({result.tithi_percent_complete:.1f}% complete)")
    print(f" Paksha          : {result.tithi_paksha}")
    print(f" Nakshatra       : {result.nakshatra_name} (Pada {result.nakshatra_pada}), "
          f"Lord: {result.nakshatra_lord}")
    print(f" Yoga            : {result.yoga_name}")
    print(f" Karana          : {result.karana_name}")
    print(f" Moon Sign       : {result.moon_rashi_name}")
    print(f" Sun Sign        : {result.sun_rashi_name}")
    print(f" Ritu (Season)   : {result.ritu_name}")
    print(f" Ayana           : {result.ayana}")
    if result.sunrise_local and result.sunset_local:
        print(f" Sunrise         : {result.sunrise_local.strftime('%H:%M:%S')}")
        print(f" Sunset          : {result.sunset_local.strftime('%H:%M:%S')}")
    print(f" Ayanamsa (Lahiri): {result.ayanamsa:.4f} degrees")
    print(line)

    if show_dasha:
        birth_dt = datetime(inp.year, inp.month, inp.day, inp.hour, inp.minute, inp.second)
        seq = vimshottari_dasha_sequence(result, birth_dt)
        print(" VIMSHOTTARI MAHADASHA SEQUENCE (from Moon's Nakshatra)")
        print(line)
        for lord, start, end in seq:
            print(f"  {lord:8s}: {start.strftime('%Y-%m-%d')}  ->  {end.strftime('%Y-%m-%d')}")
        print(line)


def main():
    args = parse_args()
    inp = gather_input(args)
    result = compute_panchang(inp)
    print_report(result, show_dasha=args.dasha)


if __name__ == "__main__":
    main()
