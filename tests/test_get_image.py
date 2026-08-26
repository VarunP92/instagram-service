import base64
import json

from src.handlers import get_image, upload
from tests.conftest import TINY_PNG_BASE64, TINY_PNG_BYTES, make_event


def _upload_one():
    event = make_event(body={
        "user_id": "user-1",
        "filename": "cat.png",
        "content_type": "image/png",
        "image_base64": TINY_PNG_BASE64,
        "tags": ["cat"],
    })

    return json.loads(
        upload.lambda_handler(event, None)["body"]
    )


def test_get_image_metadata_with_url(aws_infra):
    created = _upload_one()

    response = get_image.lambda_handler(
        make_event(
            path_params={
                "image_id": created["image_id"]
            }
        ),
        None,
    )

    assert response["statusCode"] == 200

    body = json.loads(response["body"])

    assert body["image_id"] == created["image_id"]
    assert body["download_url"].startswith("http")


def test_get_image_binary_format(aws_infra):
    created = _upload_one()

    response = get_image.lambda_handler(
        make_event(
            path_params={
                "image_id": created["image_id"]
            },
            query_params={
                "format": "binary"
            },
        ),
        None,
    )

    assert response["statusCode"] == 200
    assert response["isBase64Encoded"] is True
    assert response["headers"]["Content-Type"] == "image/png"
    assert base64.b64decode(response["body"]) == TINY_PNG_BYTES


def test_get_image_not_found(aws_infra):
    response = get_image.lambda_handler(
        make_event(
            path_params={
                "image_id": "does-not-exist"
            }
        ),
        None,
    )

    assert response["statusCode"] == 404


def test_get_image_missing_path_param(aws_infra):
    response = get_image.lambda_handler(
        make_event(path_params=None),
        None,
    )

    assert response["statusCode"] == 400
