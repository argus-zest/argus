from typing import Any, Dict, List, Optional
from common.geo import haversine_m

OFFICER_ROLES = {
    "NHAI": "Project Director, NHAI (illustrative)",
    "NDMC": "Executive Engineer, NDMC (illustrative)",
    "PWD": "Executive Engineer, PWD Division (illustrative)",
    "DJB": "Executive Engineer, DJB (illustrative)",
    "MCD": "Executive Engineer, MCD Zone (illustrative)",
    "ORPHAN": "District Magistrate (illustrative)",
}


def road_for_point(roads: List[Dict[str, Any]], lat: float, lng: float) -> Optional[Dict[str, Any]]:
    """Return the nearest road whose coverage_radius_m contains the point, else None."""
    best_road = None
    min_dist = float("inf")

    for road in roads:
        center = road.get("center", {})
        c_lat = center.get("lat")
        c_lng = center.get("lng")
        if c_lat is None or c_lng is None:
            continue
        radius = road.get("coverage_radius_m", 400)
        dist = haversine_m(lat, lng, c_lat, c_lng)
        if dist <= radius and dist < min_dist:
            min_dist = dist
            best_road = road

    return best_road


def resolve_jurisdiction(road: Optional[Dict[str, Any]], asset_type: Optional[str]) -> Dict[str, Any]:
    """
    Resolve jurisdiction using deterministic rules with confidence and reasons.
    Rules applied in exact order; first match wins.
    """
    reasons: List[str] = []

    def _road_info() -> str:
        if road:
            name = road.get("name", "Unknown")
            w = road.get("width_ft", "N/A")
            rc = road.get("road_class", "N/A")
            return f"Road '{name}' (class: {rc}, width: {w} ft)"
        return ""

    # Rule 1: road is None
    if road is None:
        return {
            "owner": "ORPHAN",
            "confidence": 0.30,
            "reasons": ["No road record covers this location"],
            "start_rung": 4,
            "officer_role": OFFICER_ROLES["ORPHAN"],
            "provenance_note": "rules are heuristic; verify",
        }

    # Rule 2: road.ownership_disputed is true
    if road.get("ownership_disputed", False):
        reasons.append("Ownership flagged as disputed")
        reasons.append(_road_info())
        return {
            "owner": "ORPHAN",
            "confidence": 0.40,
            "reasons": reasons,
            "start_rung": 4,
            "officer_role": OFFICER_ROLES["ORPHAN"],
            "provenance_note": "rules are heuristic; verify",
        }

    # Rule 3: road.is_national_highway
    if road.get("is_national_highway", False):
        reasons.append("National highway status designates NHAI jurisdiction")
        reasons.append(_road_info())
        return {
            "owner": "NHAI",
            "confidence": 0.90,
            "reasons": reasons,
            "start_rung": 1,
            "officer_role": OFFICER_ROLES["NHAI"],
            "provenance_note": "rules are heuristic; verify",
        }

    # Rule 4: road.in_ndmc
    if road.get("in_ndmc", False):
        reasons.append("Road falls inside NDMC municipal territory")
        reasons.append(_road_info())
        return {
            "owner": "NDMC",
            "confidence": 0.85,
            "reasons": reasons,
            "start_rung": 1,
            "officer_role": OFFICER_ROLES["NDMC"],
            "provenance_note": "rules are heuristic; verify",
        }

    # Rule 5: asset_type == "open_manhole"
    if asset_type == "open_manhole":
        reasons.append("Sewer manholes are typically Delhi Jal Board assets")
        reasons.append(_road_info())
        return {
            "owner": "DJB",
            "confidence": 0.70,
            "reasons": reasons,
            "start_rung": 1,
            "officer_role": OFFICER_ROLES["DJB"],
            "provenance_note": "rules are heuristic; verify",
        }

    # Rule 6: road.width_ft >= 60
    width = road.get("width_ft", 0)
    if width >= 60:
        reasons.append("Roads wider than 60 ft are treated as PWD roads")
        reasons.append(_road_info())
        return {
            "owner": "PWD",
            "confidence": 0.80,
            "reasons": reasons,
            "start_rung": 1,
            "officer_role": OFFICER_ROLES["PWD"],
            "provenance_note": "rules are heuristic; verify",
        }

    # Rule 7: Otherwise -> MCD
    reasons.append("Local and collector roads under 60 ft width are maintained by MCD")
    reasons.append(_road_info())
    return {
        "owner": "MCD",
        "confidence": 0.60,
        "reasons": reasons,
        "start_rung": 1,
        "officer_role": OFFICER_ROLES["MCD"],
        "provenance_note": "rules are heuristic; verify",
    }
