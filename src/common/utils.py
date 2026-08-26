import base64
import binascii
import json
import uuid
from datetime import datetime, timezone

MAX_IMAGE_SIZE_BYTES = 8 * 1024 * 1024  # 8 MB
ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/gif", "image/webp"}


class ValidationError(Exception):
    def __init__(self, message, details=None):
        super().__init__(message)
        self.message = message
        self.details = details


def parse_json_body(event):
    raw_body = event.get("body") or "{}"
    if event.get("isBase64Encoded"):
        raw_body = base64.b64decode(raw_body).decode("utf-8")
    try:
        return json.loads(raw_body)
    except (json.JSONDecodeError, TypeError):
        raise ValidationError("Request body must be valid JSON")


def get_query_params(event):
    return event.get("queryStringParameters") or {}


def get_path_param(event, name):
    path_params = event.get("pathParameters") or {}
    return path_params.get(name)


def new_image_id():
    return str(uuid.uuid4())


def now_iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def decode_image_base64(image_base64):
    if not image_base64:
        raise ValidationError("image_base64 is required")

    if "," in image_base64 and image_base64.strip().startswith("data:"):
        image_base64 = image_base64.split(",", 1)[1]

    try:
        image_bytes = base64.b64decode(image_base64, validate=True)
    except (binascii.Error, ValueError):
        raise ValidationError("image_base64 is not valid base64 data")

    if len(image_bytes) == 0:
        raise ValidationError("Decoded image is empty")

    if len(image_bytes) > MAX_IMAGE_SIZE_BYTES:
        raise ValidationError(
            f"Image exceeds maximum allowed size of {MAX_IMAGE_SIZE_BYTES} bytes"
        )

    return image_bytes


def validate_upload_payload(payload):
    required = ["user_id", "filename", "content_type", "image_base64"]
    missing = [field for field in required if not payload.get(field)]

    if missing:
        raise ValidationError(
            "Missing required field(s)",
            details={"missing_fields": missing}
        )

    if payload["content_type"] not in ALLOWED_CONTENT_TYPES:
        raise ValidationError(
            "Unsupported content_type",
            details={"allowed": sorted(ALLOWED_CONTENT_TYPES)}
        )

    tags = payload.get("tags", [])
    if tags is not None and not isinstance(tags, list):
        raise ValidationError("tags must be a list of strings")

    return payload
