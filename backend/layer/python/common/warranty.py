import calendar
from datetime import date, datetime
from typing import Any, Dict, List, Optional


def add_months(d: date, months: int) -> date:
    """Add calendar months to a date, clamping the day to the last day of the target month."""
    new_year = d.year + (d.month - 1 + months) // 12
    new_month = (d.month - 1 + months) % 12 + 1
    max_days = calendar.monthrange(new_year, new_month)[1]
    new_day = min(d.day, max_days)
    return date(new_year, new_month, new_day)


def compute_warranty(contract: Optional[Dict[str, Any]], as_of: date) -> Dict[str, Any]:
    if not contract:
        return {
            "status": "unknown",
            "contractor_label": "",
            "completion_date": None,
            "end_date": None,
            "days_remaining": 0,
            "work_type": "",
            "clause_text": None,
            "tender_doc_key": None,
            "provenance": "",
        }

    comp_str = contract.get("completion_date")
    if not comp_str:
        return {
            "status": "unknown",
            "contractor_label": contract.get("contractor_label", ""),
            "completion_date": None,
            "end_date": None,
            "days_remaining": 0,
            "work_type": contract.get("work_type", ""),
            "clause_text": contract.get("maintenance_clause_text"),
            "tender_doc_key": contract.get("tender_doc_key"),
            "provenance": contract.get("provenance", ""),
        }

    comp_date = datetime.strptime(comp_str, "%Y-%m-%d").date()
    defect_months = int(contract.get("defect_liability_months", 0))
    end_d = add_months(comp_date, defect_months)
    days_rem = (end_d - as_of).days

    status = "in_warranty" if days_rem >= 0 else "expired"

    return {
        "status": status,
        "contractor_label": contract.get("contractor_label", ""),
        "completion_date": comp_str,
        "end_date": end_d.isoformat(),
        "days_remaining": days_rem,
        "work_type": contract.get("work_type", ""),
        "clause_text": contract.get("maintenance_clause_text"),
        "tender_doc_key": contract.get("tender_doc_key"),
        "provenance": contract.get("provenance", ""),
    }


def find_latest_contract(contracts: List[Dict[str, Any]], road_id: str) -> Optional[Dict[str, Any]]:
    """If multiple contracts match a road, pick the one with the latest completion_date."""
    matching = [c for c in contracts if c.get("road_id") == road_id]
    if not matching:
        return None
    return max(matching, key=lambda c: c.get("completion_date", ""))
