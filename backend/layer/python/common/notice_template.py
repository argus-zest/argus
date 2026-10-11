import json
import os
from typing import Any, Dict, List, Optional


def get_legal_refs() -> List[Dict[str, str]]:
    path = os.path.join(os.path.dirname(__file__), "..", "civic_data", "legal_refs.json")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def get_recipient_role(case: Dict[str, Any], rung: int) -> str:
    jurisdiction = case.get("jurisdiction") or {}
    owner = case.get("owner") or jurisdiction.get("owner", "")
    if owner == "ORPHAN" or rung == 4:
        return "District Magistrate (illustrative)"
    elif rung == 1:
        return jurisdiction.get("officer_role", "Executive Engineer (illustrative)")
    elif rung == 2:
        return "Nodal Officer under the Flood Control Order (illustrative)"
    elif rung == 3:
        return "Superintending/Chief Engineer of the owning agency (illustrative)"
    return "District Magistrate (illustrative)"


def build_notice(
    case: Dict[str, Any],
    rung: int,
    kind: str,
    prior_notices_dates: Optional[List[str]] = None,
    photo_url: Optional[str] = None,
) -> Dict[str, str]:
    case_id = case.get("case_id", "CS-UNKNOWN")
    lat = case.get("lat", 28.6139)
    lng = case.get("lng", 77.2090)
    hotspot_id = case.get("hotspot_id") or "reported location"
    location_name = hotspot_id.replace("_", " ").title()

    osm_url = f"https://www.openstreetmap.org/?mlat={lat}&mlon={lng}#map=18/{lat}/{lng}"

    analysis = case.get("analysis") or {}
    hazard_type = analysis.get("hazard_type")
    severity = analysis.get("severity")
    submerged = analysis.get("submerged", False)
    submerged_str = "Yes" if submerged else "No"

    jurisdiction = case.get("jurisdiction") or {}
    owner = case.get("owner") or jurisdiction.get("owner", "PWD")
    confidence = jurisdiction.get("confidence", 0.8)
    conf_pct = int(confidence * 100)
    recipient_role = get_recipient_role(case, rung)

    warranty = case.get("warranty") or {}
    war_status = warranty.get("status", "unknown")
    contractor = warranty.get("contractor_label")
    end_date = warranty.get("end_date")
    days_remaining = warranty.get("days_remaining", 0)
    clause = warranty.get("clause_text") or warranty.get("maintenance_clause_text")

    # Deadline by rung: Rung 1: 3 days, Rung 2: 2 days, Rung 3: 2 days, Rung 4: 3 days
    deadline_days = 3 if rung in [1, 4] else 2

    lines = [
        "DRY-RUN: this notice was NOT sent to any official.",
        f"Case ID: {case_id}",
        f"Location: {location_name} — {osm_url}",
    ]

    legacy_manual_fallback = (
        analysis.get("description") == "Citizen reported hazard (photo omitted or manual override)"
        or analysis.get("visible_evidence") == "Manual citizen report"
    )
    if analysis and analysis.get("source") == "local_mock" and hazard_type and severity is not None:
        lines.append(f"Hazard: Local mock (not AI): {hazard_type} (recorded severity: {severity}/5)")
    elif analysis and not legacy_manual_fallback and hazard_type and severity is not None:
        lines.append(f"Hazard: {hazard_type} (Recorded severity: {severity}/5, Submerged: {submerged_str})")
    elif case.get("photo_key"):
        lines.append("Hazard: AI analysis unavailable; no severity assessment is recorded.")
    else:
        lines.append("Hazard: No photo assessment was submitted; severity is not assessed.")

    if photo_url:
        lines.append(f"Photo Evidence: {photo_url}")

    lines.append(f"Agency & Recipient: {owner} — {recipient_role} (Confidence: {conf_pct}%)")

    if war_status == "unknown" or not contractor:
        lines.append("Contractor & Warranty: The contractor and warranty could not be determined.")
    else:
        war_line = f"Contractor & Warranty: {contractor} — Status: {war_status}"
        if end_date:
            war_line += f" (End: {end_date}, Days Remaining: {days_remaining})"
        lines.append(war_line)

    if clause:
        lines.append(f'Maintenance Clause: "{clause}"')

    lines.append("Demand: Please inspect and repair, and reply with a geo-tagged photo of the repaired spot.")
    lines.append(f"Deadline: Please inspect and remediate within {deadline_days} days.")

    if rung >= 2:
        if prior_notices_dates and len(prior_notices_dates) > 0:
            dates_str = ", ".join(prior_notices_dates)
            lines.append(f"Prior Notices: Prior notice(s) were dispatched on {dates_str}.")
        else:
            lines.append("Prior Notices: A prior complaint notice was previously dispatched for this unresolved hazard.")

    # Legal references for rung 2 and 4
    legal_refs = get_legal_refs()
    if rung == 2:
        ref2 = next((r["text"] for r in legal_refs if r.get("ref_id") == "flood_control_order_2026"), None)
        if ref2:
            lines.append(f"Legal Reference: {ref2}")
    elif rung == 4:
        ref4 = next((r["text"] for r in legal_refs if r.get("ref_id") == "dm_convening"), None)
        if ref4:
            lines.append(f"Legal Reference: {ref4}")

    lines.append("Footer: Generated by Argus (hackathon prototype)")

    subject = f"[DRY-RUN] Road Hazard Repair Notice — Case {case_id} (Rung {rung})"

    return {
        "subject": subject,
        "body": "\n\n".join(lines),
    }
