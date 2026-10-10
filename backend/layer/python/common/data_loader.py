import json
from pathlib import Path
from typing import Any, Dict, List

_CACHE: Dict[str, Any] = {}


def _get_civic_data_dir() -> Path:
    return Path(__file__).resolve().parent.parent / "civic_data"


def load_civic_json(filename: str) -> Any:
    global _CACHE
    if filename in _CACHE:
        return _CACHE[filename]

    file_path = _get_civic_data_dir() / filename
    if file_path.exists():
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            _CACHE[filename] = data
            return data
    return []


def get_roads() -> List[Dict[str, Any]]:
    return load_civic_json("roads.json")


def get_hotspots() -> List[Dict[str, Any]]:
    return load_civic_json("hotspots.json")


def get_assets() -> List[Dict[str, Any]]:
    return load_civic_json("assets.json")


def get_contracts() -> List[Dict[str, Any]]:
    return load_civic_json("contracts.json")


def get_legal_refs() -> List[Dict[str, Any]]:
    return load_civic_json("legal_refs.json")


# Backward/alternative aliases
load_roads = get_roads
load_hotspots = get_hotspots
load_assets = get_assets
load_contracts = get_contracts
load_legal_refs = get_legal_refs

