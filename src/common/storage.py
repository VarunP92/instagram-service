import os
from src.common.clients import get_client

BUCKET_NAME = os.environ.get("IMAGES_BUCKET", "images-bucket")


def _s3():
    return get_client("s3")


def build_s3_key(user_id, image_id, filename):
    return f"{user_id}/{image_id}/{filename}"


def upload_image(key, image_bytes, content_type):
    _s3().put_object(
        Bucket=BUCKET_NAME,
        Key=key,
        Body=image_bytes,
        ContentType=content_type,
    )


def get_image_bytes(key):
    obj = _s3().get_object(Bucket=BUCKET_NAME, Key=key)
    return obj["Body"].read()


def delete_image(key):
    _s3().delete_object(Bucket=BUCKET_NAME, Key=key)


def generate_presigned_url(key, expires_in=3600):
    return _s3().generate_presigned_url(
        "get_object",
        Params={"Bucket": BUCKET_NAME, "Key": key},
        ExpiresIn=expires_in,
    )


def object_exists(key):
    try:
        _s3().head_object(Bucket=BUCKET_NAME, Key=key)
        return True
    except Exception:
        return False
