"""GET /images - lists image metadata with optional combinable filters."""
from src.common import db
from src.common.responses import success, error
from src.common.utils import ValidationError, get_query_params

MAX_LIMIT = 100
DEFAULT_LIMIT = 20


def parse_limit(raw_limit):
    if not raw_limit:
        return DEFAULT_LIMIT
    try:
        limit = int(raw_limit)
    except ValueError:
        raise ValidationError("limit must be an integer")
    if limit <= 0 or limit > MAX_LIMIT:
        raise ValidationError(f"limit must be between 1 and {MAX_LIMIT}")
    return limit


def lambda_handler(event, context):
    params = get_query_params(event)

    try:
        limit = parse_limit(params.get("limit"))
    except ValidationError as exc:
        return error(exc.message, status_code=400)

    try:
        items, next_token = db.list_images(
            user_id=params.get("user_id"),
            tag=params.get("tag"),
            content_type=params.get("content_type"),
            start_date=params.get("start_date"),
            end_date=params.get("end_date"),
            limit=limit,
            next_token=params.get("next_token"),
        )
    except Exception as exc:
        return error(f"Failed to list images: {exc}", status_code=502)

    return success({"items": items, "next_token": next_token, "count": len(items)})
