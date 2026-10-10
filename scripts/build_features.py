import json
import math
import sys
import time
from pathlib import Path
from typing import Any, Dict, List
import urllib.request
import urllib.error

EARTH_METRES_PER_DEG_LAT = 111320.0


def calculate_ring_coords(lat: float, lng: float, radius_m: float) -> List[tuple[float, float]]:
    delta_lat = radius_m / EARTH_METRES_PER_DEG_LAT
    cos_lat = math.cos(math.radians(lat))
    delta_lng = radius_m / (EARTH_METRES_PER_DEG_LAT * max(abs(cos_lat), 0.0001))

    # N, NE, E, SE, S, SW, W, NW
    # for 45 deg angles: cos(45) = sin(45) = 1/sqrt(2) ~ 0.70710678
    diag = 1.0 / math.sqrt(2.0)

    ring = [
        (lat + delta_lat, lng),                        # N
        (lat + delta_lat * diag, lng + delta_lng * diag), # NE
        (lat, lng + delta_lng),                        # E
        (lat - delta_lat * diag, lng + delta_lng * diag), # SE
        (lat - delta_lat, lng),                        # S
        (lat - delta_lat * diag, lng - delta_lng * diag), # SW
        (lat, lng - delta_lng),                        # W
        (lat + delta_lat * diag, lng - delta_lng * diag), # NW
    ]
    return ring


def fetch_elevations_batch(coords: List[tuple[float, float]]) -> List[float]:
    """Fetch elevations from Open-Meteo with retry and exponential backoff."""
    if not coords:
        return []

    lat_str = ",".join(f"{c[0]:.6f}" for c in coords)
    lng_str = ",".join(f"{c[1]:.6f}" for c in coords)
    url = f"https://api.open-meteo.com/v1/elevation?latitude={lat_str}&longitude={lng_str}"

    for attempt in range(3):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "ArgusDelhi/1.0"})
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                elevs = data.get("elevation", [])
                if isinstance(elevs, list):
                    return [float(e) for e in elevs]
                elif isinstance(elevs, (int, float)):
                    return [float(elevs)]
                raise ValueError("Unexpected elevation response format")
        except Exception as e:
            if attempt == 2:
                print(f"Failed to fetch elevations after 3 attempts: {e}", file=sys.stderr)
                raise
            time.sleep(2 ** attempt)

    return []


def build_features(dry_run: bool = False) -> None:
    repo_root = Path(__file__).resolve().parent.parent
    hotspots_path = repo_root / "backend" / "layer" / "python" / "civic_data" / "hotspots.json"
    params_path = repo_root / "backend" / "layer" / "python" / "civic_data" / "model_params.json"
    report_path = repo_root / "docs" / "FEATURES_REPORT.md"

    with open(hotspots_path, "r", encoding="utf-8") as f:
        hotspots: List[Dict[str, Any]] = json.load(f)

    with open(params_path, "r", encoding="utf-8") as f:
        params: Dict[str, Any] = json.load(f)

    # For each hotspot: 1 point, 8 ring200, 8 ring1500 = 17 points per hotspot.
    # Total for 10 hotspots = 170 points. Max 100 per call -> batch into chunks.
    all_coords: List[tuple[float, float]] = []
    hotspot_coord_ranges = []

    for h in hotspots:
        lat = float(h["lat"])
        lng = float(h["lng"])
        ring200 = calculate_ring_coords(lat, lng, 200.0)
        ring1500 = calculate_ring_coords(lat, lng, 1500.0)

        start_idx = len(all_coords)
        all_coords.append((lat, lng))
        all_coords.extend(ring200)
        all_coords.extend(ring1500)
        end_idx = len(all_coords)
        hotspot_coord_ranges.append((start_idx, end_idx))

    # Fetch in batches of <= 100
    elevations: List[float] = []
    chunk_size = 90
    for i in range(0, len(all_coords), chunk_size):
        chunk = all_coords[i : i + chunk_size]
        elevations.extend(fetch_elevations_batch(chunk))

    # Process each hotspot
    depressions: List[float] = []
    rel_elevs: List[float] = []
    report_rows = []

    for idx, h in enumerate(hotspots):
        s_idx, _ = hotspot_coord_ranges[idx]
        pt_elev = elevations[s_idx]
        ring200_elevs = elevations[s_idx + 1 : s_idx + 9]
        ring1500_elevs = elevations[s_idx + 9 : s_idx + 17]

        mean_ring200 = sum(ring200_elevs) / len(ring200_elevs)
        mean_ring1500 = sum(ring1500_elevs) / len(ring1500_elevs)

        elev_m = round(pt_elev, 2)
        depression_m = round(max(0.0, mean_ring200 - pt_elev), 2)
        rel_elev_m = round(pt_elev - mean_ring1500, 2)

        h["features"]["elev_m"] = elev_m
        h["features"]["depression_m"] = depression_m
        h["features"]["rel_elev_m"] = rel_elev_m

        depressions.append(depression_m)
        rel_elevs.append(rel_elev_m)

        report_rows.append(
            f"| `{h['hotspot_id']}` | {h['name']} | {elev_m} m | {depression_m} m | {rel_elev_m} m |"
        )

    # Compute mean/std over the hotspot set with floor 0.1
    n = len(hotspots)
    mean_dep = sum(depressions) / n
    std_dep = math.sqrt(sum((x - mean_dep) ** 2 for x in depressions) / n)
    std_dep = max(std_dep, 0.1)

    mean_rel = sum(rel_elevs) / n
    std_rel = math.sqrt(sum((x - mean_rel) ** 2 for x in rel_elevs) / n)
    std_rel = max(std_rel, 0.1)

    params["static"]["norm"]["depression_m"] = {
        "mean": round(mean_dep, 4),
        "std": round(std_dep, 4),
    }
    params["static"]["norm"]["rel_elev_m"] = {
        "mean": round(mean_rel, 4),
        "std": round(std_rel, 4),
    }

    if not dry_run:
        with open(hotspots_path, "w", encoding="utf-8") as f:
            json.dump(hotspots, f, indent=2)

        with open(params_path, "w", encoding="utf-8") as f:
            json.dump(params, f, indent=2)

        # Write docs/FEATURES_REPORT.md
        report_content = f"""# Features Report (docs/FEATURES_REPORT.md)

Elevation comes from a ~90 m surface model that includes buildings; use as a coarse proxy only.

## Hotspot Topography Features

| Hotspot ID | Name | Point Elevation | Local Depression (200m) | Relative Elevation (1500m) |
|---|---|---|---|---|
""" + "\n".join(report_rows) + f"""

## Computed Normalization Parameters

- **depression_m:** mean = {round(mean_dep, 4)}, std = {round(std_dep, 4)}
- **rel_elev_m:** mean = {round(mean_rel, 4)}, std = {round(std_rel, 4)}
"""
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(report_content)

        print("Features built successfully and written to hotspots.json, model_params.json, and FEATURES_REPORT.md")


if __name__ == "__main__":
    try:
        build_features()
    except Exception as exc:
        print(f"build_features failed: {exc}", file=sys.stderr)
        sys.exit(1)
