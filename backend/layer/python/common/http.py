import base64
import json
from typing import Any, Dict


class BadRequest(Exception):
    def __init__(self, message: str = "Invalid request payload"):
        super().__init__(message)
        self.message = message


def ok(body: Any, status: int = 200) -> Dict[str, Any]:
    return {
        "statusCode": status,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Content-Type,Authorization",
            "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
        },
        "body": json.dumps(body),
    }


def err(status: int, code: str, message: str) -> Dict[str, Any]:
    return {
        "statusCode": status,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Content-Type,Authorization",
            "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
        },
        "body": json.dumps({
            "error": {
                "code": code,
                "message": message,
            }
        }),
    }


def parse_json(event: Dict[str, Any]) -> Dict[str, Any]:
    body = event.get("body")
    if not body:
        raise BadRequest("Missing request body")

    if event.get("isBase64Encoded", False):
        try:
            body = base64.b64decode(body).decode("utf-8")
        except Exception as e:
            raise BadRequest(f"Failed to decode base64 body: {str(e)}")

    if isinstance(body, dict):
        return body

    try:
        parsed = json.loads(body)
        if not isinstance(parsed, dict):
            raise BadRequest("JSON body must be an object")
        return parsed
    except json.JSONDecodeError as e:
        raise BadRequest(f"Malformed JSON: {str(e)}")
