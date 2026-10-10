from datetime import datetime, timezone
import json
from common.http import ok, err


def handler(event, context):
    try:
        now_iso = datetime.now(timezone.utc).isoformat()
        return ok({"status": "ok", "time": now_iso})
    except Exception as e:
        return err(500, "INTERNAL", str(e))
