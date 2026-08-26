"""DELETE /images/{image_id} - deletes the S3 object and DynamoDB record."""
from src.common import db, storage
from src.common.responses import success, error
from src.common.utils import get_path_param, get_query_params


def lambda_handler(event, context):
    image_id = get_path_param(event, "image_id")
    if not image_id:
        return error("image_id path parameter is required", status_code=400)

    metadata = db.get_image_metadata(image_id)
    if not metadata:
        return error("Image not found", status_code=404)

    params = get_query_params(event)
    requesting_user = params.get("user_id")
    if requesting_user and requesting_user != metadata.get("user_id"):
        return error("You do not have permission to delete this image", status_code=403)

    try:
        storage.delete_image(metadata["s3_key"])
    except Exception as exc:
        return error(f"Failed to delete image from storage: {exc}", status_code=502)

    try:
        db.delete_image_metadata(image_id)
    except Exception as exc:
        return error(f"Failed to delete image metadata: {exc}", status_code=502)

    return success({"message": "Image deleted", "image_id": image_id})
