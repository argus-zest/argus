import json
import os
import re
from datetime import datetime, timezone
import boto3
from botocore.config import Config
from common.notice_template import build_notice, get_recipient_role
from common.ddb import float_to_decimal, decimal_to_float


def get_dynamodb():
    region = os.environ.get("AWS_REGION", "ap-southeast-2")
    return boto3.resource("dynamodb", region_name=region)


def get_ses():
    region = os.environ.get("AWS_REGION", "ap-southeast-2")
    return boto3.client("ses", region_name=region)


def get_s3():
    region = os.environ.get("AWS_REGION", "ap-southeast-2")
    return boto3.client(
        "s3", region_name=region,
        endpoint_url=f"https://s3.{region}.amazonaws.com",
        config=Config(signature_version="s3v4", s3={"addressing_style": "virtual"}),
    )


def try_agent_draft(case: dict, rung: int) -> dict | None:
    """Attempts agentic draft using Bedrock Converse with fallback to template."""
    backend_mode = os.environ.get("AGENT_BACKEND", "converse")
    if backend_mode != "converse":
        return None

    try:
        from common.nova import converse
        system_prompt = (
            "You draft formal, polite, factual complaint notices to Indian civic officials about road hazards. "
            "Use ONLY facts returned by the tools. Never invent names, phone numbers, tender numbers, clauses or laws. "
            "If warranty status is 'unknown', say the contractor and warranty could not be determined. "
            "Keep the body under 180 words. Output ONLY a JSON object with keys \"subject\" and \"body\"."
        )

        user_content = f"Draft an official notice for Case {case.get('case_id')} at rung {rung}. Location: {case.get('hotspot_id')}."
        messages = [{"role": "user", "content": [{"text": user_content}]}]

        resp = converse(messages=messages, system=system_prompt, max_tokens=600)
        output_text = resp.get("output", {}).get("message", {}).get("content", [{}])[0].get("text", "")

        match = re.search(r"\{.*\}", output_text, re.DOTALL)
        if match:
            parsed = json.loads(match.group(0))
            if "subject" in parsed and "body" in parsed:
                return parsed
    except Exception:
        pass
    return None


def lambda_handler(event, context):
    case_id = event.get("case_id")
    rung = int(event.get("rung", 1))

    if not case_id:
        raise ValueError("case_id is required")

    ddb = get_dynamodb()
    cases_table = ddb.Table(os.environ.get("TABLE_CASES", "argus-Cases"))
    events_table = ddb.Table(os.environ.get("TABLE_EVENTS", "argus-CaseEvents"))

    case_resp = cases_table.get_item(Key={"case_id": case_id})
    if "Item" not in case_resp:
        raise ValueError(f"Case {case_id} not found")

    case_data = decimal_to_float(case_resp["Item"])

    # Fetch prior notice events to include dates
    events_resp = events_table.query(
        KeyConditionExpression="case_id = :cid",
        ExpressionAttributeValues={":cid": case_id},
    )
    prior_events = [decimal_to_float(it) for it in events_resp.get("Items", [])]
    prior_notices_dates = [
        it["ts_seq"].split("#")[0].split("T")[0]
        for it in prior_events
        if it.get("type") in ["NOTICE_SENT", "REMINDER_SENT", "ESCALATED"]
    ]

    # Presign photo URL if photo exists
    photo_url = None
    photo_key = case_data.get("photo_key")
    if photo_key:
        try:
            s3 = get_s3()
            bucket = os.environ.get("BUCKET", "argus-uploads")
            photo_url = s3.generate_presigned_url(
                "get_object",
                Params={"Bucket": bucket, "Key": photo_key},
                ExpiresIn=86400,
            )
        except Exception:
            pass

    # Try agent draft; fall back to deterministic template
    generator = "agent"
    notice = try_agent_draft(case_data, rung)
    if not notice or not notice.get("body") or not notice.get("subject"):
        generator = "template_fallback"
        kind = "initial" if rung == case_data.get("rung", 1) else "escalation"
        notice = build_notice(
            case_data,
            rung,
            kind,
            prior_notices_dates=prior_notices_dates,
            photo_url=photo_url,
        )

    subject = notice["subject"]
    if not subject.startswith("[DRY-RUN]"):
        subject = f"[DRY-RUN] {subject}"

    body = notice["body"]
    if not body.startswith("DRY-RUN:"):
        body = f"DRY-RUN: this notice was NOT sent to any official.\n\n{body}"

    # Send plain-text email via SES
    ses_from = os.environ.get("SES_FROM", "noreply@example.com")
    dryrun_inbox = os.environ.get("DRYRUN_INBOX", "dryrun@example.com")
    ses_msg_id = "dryrun-mock"

    try:
        ses = get_ses()
        ses_res = ses.send_email(
            Source=ses_from,
            Destination={"ToAddresses": [dryrun_inbox]},
            Message={
                "Subject": {"Data": subject, "Charset": "UTF-8"},
                "Body": {"Text": {"Data": body, "Charset": "UTF-8"}},
            },
        )
        ses_msg_id = ses_res.get("MessageId", "dryrun-ses")
    except Exception as ses_err:
        print(f"SES notice dry-run delivery note: {ses_err}")

    # Determine event type
    owner = case_data.get("owner", "")
    if rung == 1 and owner != "ORPHAN":
        ev_type = "NOTICE_SENT"
        ev_msg = f"Notice dispatched to {get_recipient_role(case_data, rung)}"
    elif rung == 2 and owner != "ORPHAN":
        ev_type = "REMINDER_SENT"
        ev_msg = f"Rung 2 reminder notice dispatched to {get_recipient_role(case_data, rung)}"
    else:
        ev_type = "ESCALATED"
        ev_msg = f"Escalated notice dispatched to {get_recipient_role(case_data, rung)}"

    now_iso = datetime.now(timezone.utc).isoformat()
    ts_seq = f"{now_iso}#{int(datetime.now(timezone.utc).timestamp() * 1000) % 10000:04d}"

    meta = {
        "recipient_role": get_recipient_role(case_data, rung),
        "subject": subject,
        "body": body,
        "generated_by": generator,
        "ses_message_id": ses_msg_id,
    }

    events_table.put_item(
        Item=float_to_decimal({
            "case_id": case_id,
            "ts_seq": ts_seq,
            "type": ev_type,
            "message": ev_msg,
            "rung": rung,
            "meta": meta,
        })
    )

    return {
        "subject": subject,
        "body": body,
        "recipient_role": meta["recipient_role"],
        "generator": generator,
        "ses_message_id": ses_msg_id,
    }
