import math
from typing import Any, Callable, Iterable, Optional

EARTH_RADIUS_M = 6371008.8


def haversine_m(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Calculate the great-circle distance between two points in metres."""
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lng2 - lng1)

    a = (
        math.sin(delta_phi / 2.0) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    )
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return EARTH_RADIUS_M * c


haversine = haversine_m


def nearest(
    items: Iterable[Any],
    lat: float,
    lng: float,
    key: Callable[[Any], tuple[float, float]] = lambda i: (i["lat"], i["lng"]),
) -> Optional[Any]:
    """Return the item closest to (lat, lng) by haversine distance."""
    closest_item = None
    min_dist = float("inf")

    for item in items:
        item_lat, item_lng = key(item)
        dist = haversine_m(lat, lng, item_lat, item_lng)
        if dist < min_dist:
            min_dist = dist
            closest_item = item

    return closest_item
