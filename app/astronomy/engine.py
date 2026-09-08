"""
Vedic Astronomy and Panchang Engine using Swiss Ephemeris with Lahiri Ayanamsa.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime, timedelta, date, time
from typing import Optional, Dict, Any, List, Tuple
import zoneinfo

import swisseph as swe

# Static reference definitions
TITHI_NAMES = [
    {"number": 1, "name": "Pratipada", "paksha": "shukla", "nameHi": "प्रतिपदा"},
    {"number": 2, "name": "Dwitiya", "paksha": "shukla", "nameHi": "द्वितीया"},
    {"number": 3, "name": "Tritiya", "paksha": "shukla", "nameHi": "तृतीया"},
    {"number": 4, "name": "Chaturthi", "paksha": "shukla", "nameHi": "चतुर्थी"},
    {"number": 5, "name": "Panchami", "paksha": "shukla", "nameHi": "पंचमी"},
    {"number": 6, "name": "Shashthi", "paksha": "shukla", "nameHi": "षष्ठी"},
    {"number": 7, "name": "Saptami", "paksha": "shukla", "nameHi": "सप्तमी"},
    {"number": 8, "name": "Ashtami", "paksha": "shukla", "nameHi": "अष्टमी"},
    {"number": 9, "name": "Navami", "paksha": "shukla", "nameHi": "नवमी"},
    {"number": 10, "name": "Dashami", "paksha": "shukla", "nameHi": "दशमी"},
    {"number": 11, "name": "Ekadashi", "paksha": "shukla", "nameHi": "एकादशी"},
    {"number": 12, "name": "Dwadashi", "paksha": "shukla", "nameHi": "द्वादशी"},
    {"number": 13, "name": "Trayodashi", "paksha": "shukla", "nameHi": "त्रयोदशी"},
    {"number": 14, "name": "Chaturdashi", "paksha": "shukla", "nameHi": "चतुर्दशी"},
    {"number": 15, "name": "Purnima", "paksha": "shukla", "nameHi": "पूर्णिमा"},
    {"number": 16, "name": "Pratipada", "paksha": "krishna", "nameHi": "प्रतिपदा"},
    {"number": 17, "name": "Dwitiya", "paksha": "krishna", "nameHi": "द्वितीया"},
    {"number": 18, "name": "Tritiya", "paksha": "krishna", "nameHi": "तृतीया"},
    {"number": 19, "name": "Chaturthi", "paksha": "krishna", "nameHi": "चतुर्थी"},
    {"number": 20, "name": "Panchami", "paksha": "krishna", "nameHi": "पंचमी"},
    {"number": 21, "name": "Shashthi", "paksha": "krishna", "nameHi": "षष्ठी"},
    {"number": 22, "name": "Saptami", "paksha": "krishna", "nameHi": "सप्तमी"},
    {"number": 23, "name": "Ashtami", "paksha": "krishna", "nameHi": "अष्टमी"},
    {"number": 24, "name": "Navami", "paksha": "krishna", "nameHi": "नवमी"},
    {"number": 25, "name": "Dashami", "paksha": "krishna", "nameHi": "दशमी"},
    {"number": 26, "name": "Ekadashi", "paksha": "krishna", "nameHi": "एकादशी"},
    {"number": 27, "name": "Dwadashi", "paksha": "krishna", "nameHi": "द्वादशी"},
    {"number": 28, "name": "Trayodashi", "paksha": "krishna", "nameHi": "त्रयोदशी"},
    {"number": 29, "name": "Chaturdashi", "paksha": "krishna", "nameHi": "चतुर्दशी"},
    {"number": 30, "name": "Amavasya", "paksha": "krishna", "nameHi": "अमावस्या"},
]

NAKSHATRAS = [
    {"number": 1, "key": "ashwini", "name": "Ashwini", "nameHi": "अश्विनी", "ruler": "Ketu"},
    {"number": 2, "key": "bharani", "name": "Bharani", "nameHi": "भरणी", "ruler": "Venus"},
    {"number": 3, "key": "krittika", "name": "Krittika", "nameHi": "कृत्तिका", "ruler": "Sun"},
    {"number": 4, "key": "rohini", "name": "Rohini", "nameHi": "रोहिणी", "ruler": "Moon"},
    {"number": 5, "key": "mrigashira", "name": "Mrigashira", "nameHi": "मृगशिरा", "ruler": "Mars"},
    {"number": 6, "key": "ardra", "name": "Ardra", "nameHi": "आर्द्रा", "ruler": "Rahu"},
    {"number": 7, "key": "punarvasu", "name": "Punarvasu", "nameHi": "पुनर्वसु", "ruler": "Jupiter"},
    {"number": 8, "key": "pushya", "name": "Pushya", "nameHi": "पुष्य", "ruler": "Saturn"},
    {"number": 9, "key": "ashlesha", "name": "Ashlesha", "nameHi": "आश्लेषा", "ruler": "Mercury"},
    {"number": 10, "key": "magha", "name": "Magha", "nameHi": "मघा", "ruler": "Ketu"},
    {"number": 11, "key": "purva_phalguni", "name": "Purva Phalguni", "nameHi": "पूर्वा फाल्गुनी", "ruler": "Venus"},
    {"number": 12, "key": "uttara_phalguni", "name": "Uttara Phalguni", "nameHi": "उत्तर फाल्गुनी", "ruler": "Sun"},
    {"number": 13, "key": "hasta", "name": "Hasta", "nameHi": "हस्त", "ruler": "Moon"},
    {"number": 14, "key": "chitra", "name": "Chitra", "nameHi": "चित्रा", "ruler": "Mars"},
    {"number": 15, "key": "swati", "name": "Swati", "nameHi": "स्वाति", "ruler": "Rahu"},
    {"number": 16, "key": "vishakha", "name": "Vishakha", "nameHi": "विशाखा", "ruler": "Jupiter"},
    {"number": 17, "key": "anuradha", "name": "Anuradha", "nameHi": "अनुराधा", "ruler": "Saturn"},
    {"number": 18, "key": "jyeshtha", "name": "Jyeshtha", "nameHi": "ज्येष्ठा", "ruler": "Mercury"},
    {"number": 19, "key": "mula", "name": "Mula", "nameHi": "मूल", "ruler": "Ketu"},
    {"number": 20, "key": "purva_ashadha", "name": "Purva Ashadha", "nameHi": "पूर्वाषाढ़ा", "ruler": "Venus"},
    {"number": 21, "key": "uttara_ashadha", "name": "Uttara Ashadha", "nameHi": "उत्तराषाढ़ा", "ruler": "Sun"},
    {"number": 22, "key": "shravana", "name": "Shravana", "nameHi": "श्रवण", "ruler": "Moon"},
    {"number": 23, "key": "dhanishtha", "name": "Dhanishtha", "nameHi": "धनिष्ठा", "ruler": "Mars"},
    {"number": 24, "key": "shatabhisha", "name": "Shatabhisha", "nameHi": "शतभिषा", "ruler": "Rahu"},
    {"number": 25, "key": "purva_bhadrapada", "name": "Purva Bhadrapada", "nameHi": "पूर्वाभाद्रपद", "ruler": "Jupiter"},
    {"number": 26, "key": "uttara_bhadrapada", "name": "Uttara Bhadrapada", "nameHi": "उत्तराभाद्रपद", "ruler": "Saturn"},
    {"number": 27, "key": "revati", "name": "Revati", "nameHi": "रेवती", "ruler": "Mercury"},
]

RASHIS = [
    {"key": "mesh", "name": "Mesha", "nameEn": "Aries", "nameHi": "मेष", "ruler": "Mars"},
    {"key": "vrishabh", "name": "Vrishabha", "nameEn": "Taurus", "nameHi": "वृषभ", "ruler": "Venus"},
    {"key": "mithun", "name": "Mithuna", "nameEn": "Gemini", "nameHi": "मिथुन", "ruler": "Mercury"},
    {"key": "karka", "name": "Karka", "nameEn": "Cancer", "nameHi": "कर्क", "ruler": "Moon"},
    {"key": "simha", "name": "Simha", "nameEn": "Leo", "nameHi": "सिंह", "ruler": "Sun"},
    {"key": "kanya", "name": "Kanya", "nameEn": "Virgo", "nameHi": "कन्या", "ruler": "Mercury"},
    {"key": "tula", "name": "Tula", "nameEn": "Libra", "nameHi": "तुला", "ruler": "Venus"},
    {"key": "vrishchik", "name": "Vrischika", "nameEn": "Scorpio", "nameHi": "वृश्चिक", "ruler": "Mars"},
    {"key": "dhanu", "name": "Dhanu", "nameEn": "Sagittarius", "nameHi": "धनु", "ruler": "Jupiter"},
    {"key": "makar", "name": "Makara", "nameEn": "Capricorn", "nameHi": "मकर", "ruler": "Saturn"},
    {"key": "kumbh", "name": "Kumbha", "nameEn": "Aquarius", "nameHi": "कुम्भ", "ruler": "Saturn"},
    {"key": "meen", "name": "Meena", "nameEn": "Pisces", "nameHi": "मीन", "ruler": "Jupiter"},
]

YOGAS = [
    "Vishkambha", "Priti", "Ayushman", "Saubhagya", "Shobhana", "Atiganda",
    "Sukarma", "Dhriti", "Shoola", "Ganda", "Vriddhi", "Dhruva", "Vyaghata",
    "Harshana", "Vajra", "Siddhi", "Vyatipata", "Variyana", "Parigha", "Shiva",
    "Siddha", "Sadhya", "Shubha", "Shukla", "Brahma", "Indra", "Vaidhriti",
]

VARAS = [
    {"key": "sunday", "name": "Ravivara", "nameEn": "Sunday", "nameHi": "रविवार"},
    {"key": "monday", "name": "Somavara", "nameEn": "Monday", "nameHi": "सोमवार"},
    {"key": "tuesday", "name": "Mangalavara", "nameEn": "Tuesday", "nameHi": "मंगलवार"},
    {"key": "wednesday", "name": "Budhavara", "nameEn": "Wednesday", "nameHi": "बुधवार"},
    {"key": "thursday", "name": "Guruvara", "nameEn": "Thursday", "nameHi": "गुरुवार"},
    {"key": "friday", "name": "Shukravara", "nameEn": "Friday", "nameHi": "शुक्रवार"},
    {"key": "saturday", "name": "Shanivara", "nameEn": "Saturday", "nameHi": "शनिवार"},
]

KARANAS_MOVABLE = ["Bava", "Balava", "Kaulava", "Taitila", "Garaja", "Vanija", "Vishti"]
KARANAS_FIXED = {0: "Kimstughna", 57: "Shakuni", 58: "Chatushpada", 59: "Naga"}

VIMSHOTTARI_YEARS = {
    "Ketu": 7, "Venus": 20, "Sun": 6, "Moon": 10, "Mars": 7,
    "Rahu": 18, "Jupiter": 16, "Saturn": 19, "Mercury": 17,
}
VIMSHOTTARI_ORDER = ["Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury"]


class VedicAstronomyEngine:
    """Astronomical Engine implementing Lahiri Sidereal calculations with Swiss Ephemeris."""

    @staticmethod
    def calculate_panchang(
        target_date: date,
        target_time: time = time(6, 0),
        latitude: float = 28.6139,
        longitude: float = 77.2090,
        tz_offset_hours: float = 5.5,
    ) -> Dict[str, Any]:
        dt = datetime.combine(target_date, target_time)
        ut_dt = dt - timedelta(hours=tz_offset_hours)
        hour_dec = ut_dt.hour + ut_dt.minute / 60.0 + ut_dt.second / 3600.0
        jd_ut = swe.julday(ut_dt.year, ut_dt.month, ut_dt.day, hour_dec, swe.GREG_CAL)

        swe.set_sid_mode(swe.SIDM_LAHIRI, 0, 0)
        ayanamsa = swe.get_ayanamsa_ut(jd_ut)
        flags = swe.FLG_SWIEPH | swe.FLG_SIDEREAL

        sun_pos, _ = swe.calc_ut(jd_ut, swe.SUN, flags)
        moon_pos, _ = swe.calc_ut(jd_ut, swe.MOON, flags)

        sun_long = sun_pos[0] % 360.0
        moon_long = moon_pos[0] % 360.0

        # Tithi calculation (12 degree segments)
        diff = (moon_long - sun_long) % 360.0
        tithi_idx = int(diff // 12)
        tithi_meta = TITHI_NAMES[tithi_idx]
        tithi_comp = round(((diff % 12) / 12.0) * 100.0, 1)

        # Vara (weekday)
        vara_idx = (dt.weekday() + 1) % 7  # 0=Sunday
        vara_meta = VARAS[vara_idx]

        # Nakshatra (13 deg 20 min segments = 360 / 27)
        nak_span = 360.0 / 27.0
        nak_idx = int(moon_long // nak_span)
        nak_meta = NAKSHATRAS[nak_idx]
        pada = int((moon_long % nak_span) // (nak_span / 4)) + 1

        # Yoga (sum of Sun and Moon / 13d 20m)
        yoga_deg = (sun_long + moon_long) % 360.0
        yoga_idx = int(yoga_deg // nak_span)
        yoga_name = YOGAS[yoga_idx]

        # Karana (half tithi = 6 degree segments)
        karana_idx = int(diff // 6)
        if karana_idx in KARANAS_FIXED:
            karana_name = KARANAS_FIXED[karana_idx]
        else:
            karana_name = KARANAS_MOVABLE[(karana_idx - 1) % 7]

        # Rashis (30 degree segments)
        moon_rashi_idx = int(moon_long // 30)
        sun_rashi_idx = int(sun_long // 30)
        moon_rashi = RASHIS[moon_rashi_idx]
        sun_rashi = RASHIS[sun_rashi_idx]

        # Sunrise / Sunset
        sunrise_str, sunset_str = None, None
        try:
            jd_midnight = swe.julday(target_date.year, target_date.month, target_date.day, 0.0, swe.GREG_CAL) - tz_offset_hours / 24.0
            geopos = (longitude, latitude, 0.0)
            _, rise_t = swe.rise_trans(jd_midnight, swe.SUN, swe.CALC_RISE, geopos)
            _, set_t = swe.rise_trans(jd_midnight, swe.SUN, swe.CALC_SET, geopos)
            
            y, m, d, h = swe.revjul(rise_t[0], swe.GREG_CAL)
            sr_dt = datetime(y, m, d) + timedelta(hours=h + tz_offset_hours)
            sunrise_str = sr_dt.strftime("%H:%M:%S")

            y, m, d, h = swe.revjul(set_t[0], swe.GREG_CAL)
            ss_dt = datetime(y, m, d) + timedelta(hours=h + tz_offset_hours)
            sunset_str = ss_dt.strftime("%H:%M:%S")
        except Exception:
            pass

        return {
            "date": target_date.isoformat(),
            "location": {
                "latitude": latitude,
                "longitude": longitude,
                "tz_offset_hours": tz_offset_hours,
            },
            "vara": vara_meta,
            "tithi": {
                "number": tithi_meta["number"],
                "name": tithi_meta["name"],
                "nameHi": tithi_meta["nameHi"],
                "paksha": tithi_meta["paksha"],
                "completionPercent": tithi_comp,
            },
            "nakshatra": {
                "number": nak_meta["number"],
                "key": nak_meta["key"],
                "name": nak_meta["name"],
                "nameHi": nak_meta["nameHi"],
                "pada": pada,
                "ruler": nak_meta["ruler"],
            },
            "yoga": {
                "number": yoga_idx + 1,
                "name": yoga_name,
            },
            "karana": {
                "number": karana_idx + 1,
                "name": karana_name,
            },
            "rashi": {
                "moon": moon_rashi,
                "sun": sun_rashi,
            },
            "sunrise": sunrise_str,
            "sunset": sunset_str,
            "calculation": {
                "system": "sidereal",
                "ayanamsa": "lahiri",
                "ayanamsaDegrees": round(ayanamsa, 4),
                "sunLongitude": round(sun_long, 4),
                "moonLongitude": round(moon_long, 4),
            },
        }

    @staticmethod
    def calculate_birth_chart(
        birth_date: date,
        birth_time: time,
        latitude: float,
        longitude: float,
        tz_offset_hours: float = 5.5,
    ) -> Dict[str, Any]:
        """Calculates full Vedic birth chart details and Vimshottari Mahadasha sequence."""
        panchang = VedicAstronomyEngine.calculate_panchang(
            target_date=birth_date,
            target_time=birth_time,
            latitude=latitude,
            longitude=longitude,
            tz_offset_hours=tz_offset_hours,
        )

        nak_span = 360.0 / 27.0
        moon_long = panchang["calculation"]["moonLongitude"]
        portion_into_nak = (moon_long % nak_span) / nak_span

        nak_number = panchang["nakshatra"]["number"] - 1
        start_lord_idx = nak_number % 9
        start_lord = VIMSHOTTARI_ORDER[start_lord_idx]

        balance_fraction = 1.0 - portion_into_nak
        balance_years = VIMSHOTTARI_YEARS[start_lord] * balance_fraction

        birth_dt = datetime.combine(birth_date, birth_time)
        sequence = []

        curr_start = birth_dt
        curr_end = curr_start + timedelta(days=balance_years * 365.2425)
        sequence.append({
            "planet": start_lord,
            "start": curr_start.strftime("%Y-%m-%d"),
            "end": curr_end.strftime("%Y-%m-%d"),
            "durationYears": round(balance_years, 2),
            "isBirthBalance": True,
        })

        curr_start = curr_end
        idx = start_lord_idx
        for _ in range(8):
            idx = (idx + 1) % 9
            lord = VIMSHOTTARI_ORDER[idx]
            yrs = VIMSHOTTARI_YEARS[lord]
            curr_end = curr_start + timedelta(days=yrs * 365.2425)
            sequence.append({
                "planet": lord,
                "start": curr_start.strftime("%Y-%m-%d"),
                "end": curr_end.strftime("%Y-%m-%d"),
                "durationYears": yrs,
                "isBirthBalance": False,
            })
            curr_start = curr_end

        return {
            "birthDetails": {
                "date": birth_date.isoformat(),
                "time": birth_time.isoformat(),
                "latitude": latitude,
                "longitude": longitude,
                "tzOffsetHours": tz_offset_hours,
            },
            "panchang": panchang,
            "rashi": panchang["rashi"],
            "nakshatra": panchang["nakshatra"],
            "dasha": {
                "system": "vimshottari",
                "birthMahadasha": {
                    "planet": start_lord,
                    "balanceYears": round(balance_years, 2),
                },
                "sequence": sequence,
            },
            "calculation": panchang["calculation"],
        }
