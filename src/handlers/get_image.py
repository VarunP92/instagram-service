"""GET /images/{image_id} - returns metadata + presigned URL, or raw bytes."""
import base64

from src.common import db, storage
from src.common.responses import build_response, error
from src.common.utils import get_path_param, get_query_params


def lambda_handler(event, context):
    image_id = get_path_param(event, "image_id")
    if not image_id:
        return error("image_id path parameter is required", status_code=400)

    metadata = db.get_image_metadata(image_id)
    if not metadata:
        return error("Image not found", status_code=404)

    params = get_query_params(event)
    response_format = (params.get("format") or "url").lower()

    if response_format == "binary":
        try:
            image_bytes = storage.get_image_bytes(metadata["s3_key"])
        except Exception as exc:
            return error(f"Failed to fetch image content: {exc}", status_code=502)

        encoded_body = base64.b64encode(image_bytes).decode("utf-8")
        headers = {
            "Content-Type": metadata.get("content_type", "application/octet-stream"),
            "Content-Disposition": f'attachment; filename="{metadata.get("filename", image_id)}"',
        }
        return build_response(200, encoded_body, extra_headers=headers, is_binary=True)

    try:
        download_url = storage.generate_presigned_url(metadata["s3_key"])
    except Exception as exc:
        return error(f"Failed to generate download URL: {exc}", status_code=502)

    body = dict(metadata)
    body["download_url"] = download_url
    return build_response(200, body)
