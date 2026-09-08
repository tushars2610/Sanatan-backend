"""
places.py
---------
A tiny offline place lookup so the project works without any internet
access. It ships with a small database of common Indian cities/towns
(including the ones used in our examples). If a place isn't found, the
user is simply asked to type latitude, longitude, and UTC offset directly.

Feel free to add more entries to CITY_DB — format is:
    "city name (lowercase)": (latitude, longitude, tz_offset_hours)
"""

from __future__ import annotations

CITY_DB: dict[str, tuple[float, float, float]] = {
    "new delhi":        (28.6139, 77.2090, 5.5),
    "delhi":            (28.7041, 77.1025, 5.5),
    "mumbai":           (19.0760, 72.8777, 5.5),
    "kolkata":          (22.5726, 88.3639, 5.5),
    "chennai":          (13.0827, 80.2707, 5.5),
    "bengaluru":        (12.9716, 77.5946, 5.5),
    "bangalore":        (12.9716, 77.5946, 5.5),
    "hyderabad":        (17.3850, 78.4867, 5.5),
    "pune":             (18.5204, 73.8567, 5.5),
    "ahmedabad":        (23.0225, 72.5714, 5.5),
    "jaipur":           (26.9124, 75.7873, 5.5),
    "lucknow":          (26.8467, 80.9462, 5.5),
    "dehradun":         (30.3165, 78.0322, 5.5),
    "tehri garhwal":    (30.3900, 78.4800, 5.5),
    "new tehri":        (30.3800, 78.4800, 5.5),
    "dhanbad":          (23.7957, 86.4304, 5.5),
    "ranchi":           (23.3441, 85.3096, 5.5),
    "jamshedpur":       (22.8046, 86.2029, 5.5),
    "patna":            (25.5941, 85.1376, 5.5),
    "bhopal":           (23.2599, 77.4126, 5.5),
    "chandigarh":       (30.7333, 76.7794, 5.5),
    "guwahati":         (26.1445, 91.7362, 5.5),
    "bhubaneswar":      (20.2961, 85.8245, 5.5),
    "kanpur":           (26.4499, 80.3319, 5.5),
    "nagpur":           (21.1458, 79.0882, 5.5),
    "indore":           (22.7196, 75.8577, 5.5),
    "surat":            (21.1702, 72.8311, 5.5),
    "varanasi":         (25.3176, 82.9739, 5.5),
    "amritsar":         (31.6340, 74.8723, 5.5),
    "srinagar":         (34.0837, 74.7973, 5.5),
    "shimla":           (31.1048, 77.1734, 5.5),
    "gurugram":         (28.4595, 77.0266, 5.5),
    "gurgaon":          (28.4595, 77.0266, 5.5),
    "noida":            (28.5355, 77.3910, 5.5),
    "haridwar":         (29.9457, 78.1642, 5.5),
    "rishikesh":        (30.0869, 78.2676, 5.5),
}


def lookup(place_name: str):
    """Return (lat, lon, tz_offset) if the place is known, else None."""
    return CITY_DB.get(place_name.strip().lower())
