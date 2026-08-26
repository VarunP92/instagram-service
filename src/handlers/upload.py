"""POST /images -- uploads an image to S3 and its metadata to DynamoDB."""
from src.common import db, storage
from src.common.responses import success, error
from src.common.utils import (
    ValidationError,
    decode_image_base64,
    new_image_id,
    now_iso,
    parse_json_body,
    validate_upload_payload,
)


def lambda_handler(event, context):
    try:
        payload = parse_json_body(event)
        validate_upload_payload(payload)
        image_bytes = decode_image_base64(payload["image_base64"])
    except ValidationError as exc:
        return error(exc.message, status_code=400, details=exc.details)

    user_id = payload["user_id"]
    filename = payload["filename"]
    content_type = payload["content_type"]

    image_id = new_image_id()
    s3_key = storage.build_s3_key(user_id, image_id, filename)

    try:
        storage.upload_image(s3_key, image_bytes, content_type)
    except Exception as exc:
        return error(f"Failed to upload image to storage: {exc}", status_code=502)

    metadata = {
        "image_id": image_id,
        "user_id": user_id,
        "filename": filename,
        "content_type": content_type,
        "size": len(image_bytes),
        "description": payload.get("description", ""),
        "tags": payload.get("tags") or [],
        "uploaded_at": now_iso(),
        "s3_key": s3_key,
        "s3_bucket": storage.BUCKET_NAME,
    }

    try:
        db.put_image_metadata(metadata)
    except Exception as exc:
        storage.delete_image(s3_key)
        return error(f"Failed to persist image metadata: {exc}", status_code=502)

    return success(metadata, status_code=201)
