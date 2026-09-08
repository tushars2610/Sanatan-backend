from typing import List, Optional
import places
from app.schemas.places import PlaceItem


class PlaceService:
    @staticmethod
    def search(query: str) -> List[PlaceItem]:
        q = query.strip().lower()
        results = []
        for city_name, (lat, lon, tz) in places.CITY_DB.items():
            if q in city_name:
                results.append(
                    PlaceItem(
                        name=city_name.title(),
                        latitude=lat,
                        longitude=lon,
                        tz_offset_hours=tz,
                        state="India",
                        country="India",
                    )
                )
        return results

    @staticmethod
    def resolve(place_name: str) -> Optional[PlaceItem]:
        q = place_name.strip().lower()
        found = places.lookup(q)
        if found:
            lat, lon, tz = found
            return PlaceItem(
                name=place_name.title(),
                latitude=lat,
                longitude=lon,
                tz_offset_hours=tz,
                state="India",
                country="India",
            )
        return None
