# Panchang Calculator

A Python project that calculates the Vedic **Panchang** (Tithi, Vara, Nakshatra,
Yoga, Karana), Moon sign, Sun sign, sunrise/sunset, and an optional
**Vimshottari Mahadasha** sequence — for any date, time, and place of birth.

It uses the [Swiss Ephemeris](https://www.astro.com/swisseph/) (via the
`pyswisseph` package) for accurate planetary positions, with the **Lahiri
Ayanamsa** (the standard sidereal ayanamsa used in Indian Panchangs).

## Project structure

```
panchang_project/
├── panchang.py       Core astronomical engine (all the math)
├── places.py         Small offline city database (lat/lon/timezone)
├── main.py           Command-line interface
├── requirements.txt
└── README.md
```

## Setup

```bash
pip install -r requirements.txt
```

(No internet connection is needed at runtime — Swiss Ephemeris's built-in
Moshier ephemeris is used, which is accurate for the +/- few thousand years
range without external data files.)

## Usage

### Interactive mode

```bash
python3 main.py
```

You'll be prompted for date, time, and place of birth.

### Command-line mode

```bash
python3 main.py --date 2001-10-26 --time 13:30 --place "Tehri Garhwal"

python3 main.py --date 1999-04-01 --time 04:00 --place Dhanbad --dasha
```

If your place isn't in the built-in database (`places.py`), you'll be asked
for latitude, longitude, and UTC offset directly — or you can pass them:

```bash
python3 main.py --date 1995-06-15 --time 09:15 \
    --lat 19.076 --lon 72.8777 --tz 5.5 --place "Custom Place"
```

### Flags

| Flag       | Description                                             |
|------------|----------------------------------------------------------|
| `--date`   | Birth date, `YYYY-MM-DD`                                  |
| `--time`   | Birth time, `HH:MM` or `HH:MM:SS` (24-hour)               |
| `--place`  | Place name (checked against the built-in database)       |
| `--lat`    | Latitude (manual override / fallback)                     |
| `--lon`    | Longitude (manual override / fallback)                    |
| `--tz`     | UTC offset in hours, e.g. `5.5` for IST                   |
| `--dasha`  | Also print the Vimshottari Mahadasha sequence             |

## Adding more cities

Edit `places.py` and add an entry to `CITY_DB`:

```python
"my city": (latitude, longitude, utc_offset_hours),
```

## What's calculated

- **Tithi** — lunar day (1–30), with Shukla/Krishna Paksha and % completion
- **Vara** — weekday
- **Nakshatra** — lunar mansion (1–27), with Pada (quarter) and ruling planet
- **Yoga** — Sun+Moon based yoga (1–27)
- **Karana** — half-tithi (1–60, cycling through 11 named karanas)
- **Moon Sign (Rashi)** and **Sun Sign**
- **Ritu** (season) and **Ayana** (solstice half)
- **Sunrise / Sunset** for the given location
- **Vimshottari Mahadasha** sequence (optional, `--dasha`), starting from the
  balance of the dasha running at birth, based on Moon's Nakshatra

## Notes & limitations

- Calculations use **sidereal (Lahiri)** positions, standard for Panchang-making
  in India. This differs from Western tropical astrology.
- The weekday (Vara) here is based on the **civil calendar date**, not the
  traditional sunrise-to-sunrise Vedic day — for births very close to midnight
  this can occasionally differ from a purist Panchang by one day.
- Ascendant (Lagna) and detailed planetary house placements are **not**
  included in this version — this focuses on core Panchang elements plus a
  basic Dasha timeline. These could be added as a future extension using the
  same Swiss Ephemeris foundation.
- Always double check important dates against a professional or a dedicated
  panchang authority — this is a solid, ephemeris-accurate tool but not a
  substitute for a qualified astrologer for major life decisions.
