"""
panchang.py
-----------
Core engine that computes the Vedic Panchang (Tithi, Vara, Nakshatra, Yoga,
Karana) plus Moon sign, Sun sign, sunrise/sunset, and other basic details
for any date, time and place, using the Swiss Ephemeris (pyswisseph).

All calculations use the Lahiri Ayanamsa (the most widely used sidereal
ayanamsa in Indian Panchang-making) and true geocentric positions.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime, timedelta

import swisseph as swe

# ---------------------------------------------------------------------------
# Static reference data
# ---------------------------------------------------------------------------

TITHI_NAMES = [
    "Shukla Pratipada", "Shukla Dwitiya", "Shukla Tritiya", "Shukla Chaturthi",
    "Shukla Panchami", "Shukla Shashthi", "Shukla Saptami", "Shukla Ashtami",
    "Shukla Navami", "Shukla Dashami", "Shukla Ekadashi", "Shukla Dwadashi",
    "Shukla Trayodashi", "Shukla Chaturdashi", "Purnima",
    "Krishna Pratipada", "Krishna Dwitiya", "Krishna Tritiya", "Krishna Chaturthi",
    "Krishna Panchami", "Krishna Shashthi", "Krishna Saptami", "Krishna Ashtami",
    "Krishna Navami", "Krishna Dashami", "Krishna Ekadashi", "Krishna Dwadashi",
    "Krishna Trayodashi", "Krishna Chaturdashi", "Amavasya",
]

NAKSHATRA_NAMES = [
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
    "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni",
    "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha",
    "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishtha",
    "Shatabhisha", "Purva Bhadrapada", "Uttara Bhadrapada", "Revati",
]

NAKSHATRA_LORDS = [
    "Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury",
] * 3  # cycles every 9 nakshatras (Vimshottari Dasha lord sequence)

YOGA_NAMES = [
    "Vishkambha", "Priti", "Ayushman", "Saubhagya", "Shobhana", "Atiganda",
    "Sukarma", "Dhriti", "Shoola", "Ganda", "Vriddhi", "Dhruva", "Vyaghata",
    "Harshana", "Vajra", "Siddhi", "Vyatipata", "Variyana", "Parigha", "Shiva",
    "Siddha", "Sadhya", "Shubha", "Shukla", "Brahma", "Indra", "Vaidhriti",
]

KARANA_NAMES_MOVABLE = ["Bava", "Balava", "Kaulava", "Taitila", "Garaja", "Vanija", "Vishti"]
KARANA_NAMES_FIXED = ["Shakuni", "Chatushpada", "Naga", "Kimstughna"]

RASHI_NAMES = [
    "Mesha (Aries)", "Vrishabha (Taurus)", "Mithuna (Gemini)", "Karka (Cancer)",
    "Simha (Leo)", "Kanya (Virgo)", "Tula (Libra)", "Vrischika (Scorpio)",
    "Dhanu (Sagittarius)", "Makara (Capricorn)", "Kumbha (Aquarius)", "Meena (Pisces)",
]

VARA_NAMES = [
    "Ravivara (Sunday)", "Somavara (Monday)", "Mangalavara (Tuesday)",
    "Budhavara (Wednesday)", "Guruvara (Thursday)", "Shukravara (Friday)",
    "Shanivara (Saturday)",
]

RITU_NAMES = ["Vasant (Spring)", "Grishma (Summer)", "Varsha (Monsoon)",
              "Sharad (Autumn)", "Hemant (Pre-winter)", "Shishir (Winter)"]

VIMSHOTTARI_YEARS = {
    "Ketu": 7, "Venus": 20, "Sun": 6, "Moon": 10, "Mars": 7,
    "Rahu": 18, "Jupiter": 16, "Saturn": 19, "Mercury": 17,
}
VIMSHOTTARI_ORDER = ["Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury"]
TOTAL_DASHA_YEARS = sum(VIMSHOTTARI_YEARS.values())  # 120


@dataclass
class BirthInput:
    year: int
    month: int
    day: int
    hour: int
    minute: int
    second: int = 0
    tz_offset_hours: float = 5.5   # e.g. 5.5 for India Standard Time
    latitude: float = 0.0
    longitude: float = 0.0
    place_name: str = ""


@dataclass
class PanchangResult:
    input: BirthInput
    julian_day_ut: float
    sun_longitude: float
    moon_longitude: float
    tithi_index: int
    tithi_name: str
    tithi_paksha: str
    tithi_number_in_paksha: int
    tithi_percent_complete: float
    vara_index: int
    vara_name: str
    nakshatra_index: int
    nakshatra_name: str
    nakshatra_lord: str
    nakshatra_pada: int
    yoga_index: int
    yoga_name: str
    karana_index: int
    karana_name: str
    moon_rashi_index: int
    moon_rashi_name: str
    sun_rashi_index: int
    sun_rashi_name: str
    ritu_name: str
    ayana: str
    sunrise_local: datetime | None
    sunset_local: datetime | None
    ayanamsa: float


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def _to_julian_day_ut(inp: BirthInput) -> float:
    """Convert local civil date/time + timezone offset to Julian Day (UT)."""
    local_dt = datetime(inp.year, inp.month, inp.day, inp.hour, inp.minute, inp.second)
    ut_dt = local_dt - timedelta(hours=inp.tz_offset_hours)
    hour_decimal = ut_dt.hour + ut_dt.minute / 60.0 + ut_dt.second / 3600.0
    return swe.julday(ut_dt.year, ut_dt.month, ut_dt.day, hour_decimal, swe.GREG_CAL)


def _sidereal_longitude(jd_ut: float, body: int) -> float:
    """Sidereal (Lahiri) ecliptic longitude of a body, 0-360 degrees."""
    swe.set_sid_mode(swe.SIDM_LAHIRI, 0, 0)
    flags = swe.FLG_SWIEPH | swe.FLG_SIDEREAL
    xx, _ret = swe.calc_ut(jd_ut, body, flags)
    return xx[0] % 360.0


def _normalize(angle: float) -> float:
    a = angle % 360.0
    return a + 360.0 if a < 0 else a


def _julian_to_local_datetime(jd_ut: float, tz_offset_hours: float) -> datetime:
    y, m, d, h = swe.revjul(jd_ut, swe.GREG_CAL)
    base = datetime(y, m, d) + timedelta(hours=h)
    return base + timedelta(hours=tz_offset_hours)


def _sunrise_sunset(inp: BirthInput, jd_ut: float):
    """Returns (sunrise_local, sunset_local) as datetime objects, or (None, None)."""
    geopos = (inp.longitude, inp.latitude, 0.0)
    # search from local midnight (in UT) for that calendar day
    jd_midnight = swe.julday(inp.year, inp.month, inp.day, 0.0, swe.GREG_CAL) - inp.tz_offset_hours / 24.0
    try:
        _res, tret_rise = swe.rise_trans(jd_midnight, swe.SUN, swe.CALC_RISE, geopos)
        _res2, tret_set = swe.rise_trans(jd_midnight, swe.SUN, swe.CALC_SET, geopos)
        sunrise = _julian_to_local_datetime(tret_rise[0], inp.tz_offset_hours)
        sunset = _julian_to_local_datetime(tret_set[0], inp.tz_offset_hours)
        return sunrise, sunset
    except Exception:
        return None, None


# ---------------------------------------------------------------------------
# Main computation
# ---------------------------------------------------------------------------

def compute_panchang(inp: BirthInput) -> PanchangResult:
    jd_ut = _to_julian_day_ut(inp)

    swe.set_sid_mode(swe.SIDM_LAHIRI, 0, 0)
    ayanamsa = swe.get_ayanamsa_ut(jd_ut)

    sun_long = _sidereal_longitude(jd_ut, swe.SUN)
    moon_long = _sidereal_longitude(jd_ut, swe.MOON)

    # ---- Tithi ----
    diff = _normalize(moon_long - sun_long)
    tithi_index = int(diff // 12)  # 0-29
    tithi_percent = (diff % 12) / 12.0 * 100.0
    tithi_name = TITHI_NAMES[tithi_index]
    paksha = "Shukla Paksha" if tithi_index < 15 else "Krishna Paksha"
    tithi_num_in_paksha = (tithi_index % 15) + 1

    # ---- Vara (weekday) ----
    # Vedic day starts at sunrise, but for a simple/standard implementation
    # we use the civil calendar weekday of the given local date.
    local_dt = datetime(inp.year, inp.month, inp.day)
    vara_index = (local_dt.weekday() + 1) % 7  # Python Mon=0 -> convert so Sun=0
    vara_name = VARA_NAMES[vara_index]

    # ---- Nakshatra ----
    nak_span = 360.0 / 27.0  # 13d20'
    nakshatra_index = int(moon_long // nak_span)
    nakshatra_name = NAKSHATRA_NAMES[nakshatra_index]
    nakshatra_lord = NAKSHATRA_LORDS[nakshatra_index]
    pada = int((moon_long % nak_span) // (nak_span / 4)) + 1

    # ---- Yoga ----
    yoga_val = _normalize(sun_long + moon_long)
    yoga_span = 360.0 / 27.0
    yoga_index = int(yoga_val // yoga_span)
    yoga_name = YOGA_NAMES[yoga_index]

    # ---- Karana (half-tithi, 0-59) ----
    # Karana 0 is always the fixed "Kimstughna"; karanas 57,58,59 are the
    # fixed "Shakuni", "Chatushpada", "Naga"; the 56 in between (1-56) cycle
    # through the 7 movable karanas repeated 8 times.
    karana_num = int(diff // 6)  # 0-59
    fixed_map = {0: "Kimstughna", 57: "Shakuni", 58: "Chatushpada", 59: "Naga"}
    if karana_num in fixed_map:
        karana_name = fixed_map[karana_num]
    else:
        karana_name = KARANA_NAMES_MOVABLE[(karana_num - 1) % 7]

    # ---- Rashi (Moon sign / Sun sign) ----
    moon_rashi_index = int(moon_long // 30)
    sun_rashi_index = int(sun_long // 30)

    # ---- Ritu (season) based on sidereal solar month, 2 rashis per ritu ----
    ritu_name = RITU_NAMES[(sun_rashi_index // 2) % 6]

    # ---- Ayana ----
    # Uttarayana: Sun sidereal longitude from Makara(270) through Mithuna end (~180..270 wrap)
    ayana = "Uttarayana" if sun_rashi_index in (9, 10, 11, 0, 1, 2) else "Dakshinayana"

    sunrise_local, sunset_local = _sunrise_sunset(inp, jd_ut)

    return PanchangResult(
        input=inp,
        julian_day_ut=jd_ut,
        sun_longitude=sun_long,
        moon_longitude=moon_long,
        tithi_index=tithi_index,
        tithi_name=tithi_name,
        tithi_paksha=paksha,
        tithi_number_in_paksha=tithi_num_in_paksha,
        tithi_percent_complete=tithi_percent,
        vara_index=vara_index,
        vara_name=vara_name,
        nakshatra_index=nakshatra_index,
        nakshatra_name=nakshatra_name,
        nakshatra_lord=nakshatra_lord,
        nakshatra_pada=pada,
        yoga_index=yoga_index,
        yoga_name=yoga_name,
        karana_index=karana_num,
        karana_name=karana_name,
        moon_rashi_index=moon_rashi_index,
        moon_rashi_name=RASHI_NAMES[moon_rashi_index],
        sun_rashi_index=sun_rashi_index,
        sun_rashi_name=RASHI_NAMES[sun_rashi_index],
        ritu_name=ritu_name,
        ayana=ayana,
        sunrise_local=sunrise_local,
        sunset_local=sunset_local,
        ayanamsa=ayanamsa,
    )


# ---------------------------------------------------------------------------
# Vimshottari Dasha (basic, from Moon's Nakshatra at birth)
# ---------------------------------------------------------------------------

def vimshottari_dasha_sequence(result: PanchangResult, birth_datetime_local: datetime, levels: int = 9):
    """Return the sequence of Mahadasha periods (lord, start_date, end_date)
    starting with the *balance* of the dasha running at birth."""
    nak_span = 360.0 / 27.0
    moon_long = result.moon_longitude
    portion_into_nakshatra = (moon_long % nak_span) / nak_span  # 0..1
    start_lord_index = result.nakshatra_index % 9
    start_lord = VIMSHOTTARI_ORDER[start_lord_index]

    balance_fraction = 1.0 - portion_into_nakshatra
    balance_years = VIMSHOTTARI_YEARS[start_lord] * balance_fraction

    sequence = []
    current_date = birth_datetime_local
    end_date = current_date + timedelta(days=balance_years * 365.2425)
    sequence.append((start_lord, current_date, end_date))
    current_date = end_date

    idx = start_lord_index
    for _ in range(levels - 1):
        idx = (idx + 1) % 9
        lord = VIMSHOTTARI_ORDER[idx]
        yrs = VIMSHOTTARI_YEARS[lord]
        end_date = current_date + timedelta(days=yrs * 365.2425)
        sequence.append((lord, current_date, end_date))
        current_date = end_date

    return sequence
