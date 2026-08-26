import base64
import json

from src.handlers import upload
from tests.conftest import TINY_PNG_BASE64, make_event


def test_upload_success(aws_infra):
    event = make_event(body={
        "user_id": "user-1",
        "filename": "cat.png",
        "content_type": "image/png",
        "image_base64": TINY_PNG_BASE64,
        "description": "A cat",
        "tags": ["cat", "cute"],
    })

    response = upload.lambda_handler(event, None)

    assert response["statusCode"] == 201
    body = json.loads(response["body"])
    assert body["user_id"] == "user-1"
    assert body["tags"] == ["cat", "cute"]
    assert "image_id" in body
    assert body["s3_key"].startswith("user-1/")
    assert body["size"] > 0


def test_upload_missing_required_fields(aws_infra):
    response = upload.lambda_handler(
        make_event(body={"user_id": "user-1"}),
        None
    )

    assert response["statusCode"] == 400
    body = json.loads(response["body"])
    assert set(body["details"]["missing_fields"]) == {
        "filename",
        "content_type",
        "image_base64",
    }


def test_upload_unsupported_content_type(aws_infra):
    event = make_event(body={
        "user_id": "user-1",
        "filename": "movie.mp4",
        "content_type": "video/mp4",
        "image_base64": TINY_PNG_BASE64,
    })

    response = upload.lambda_handler(event, None)

    assert response["statusCode"] == 400
    assert json.loads(response["body"])["error"] == "Unsupported content type"


def test_upload_invalid_base64(aws_infra):
    event = make_event(body={
        "user_id": "user-1",
        "filename": "cat.png",
        "content_type": "image/png",
        "image_base64": "not-valid-base64!!!",
    })

    response = upload.lambda_handler(event, None)

    assert response["statusCode"] == 400
    assert "base64" in json.loads(response["body"])["error"]


def test_upload_oversized_image_rejected(aws_infra, monkeypatch):
    import src.common.utils as utils_module

    monkeypatch.setattr(utils_module, "MAX_IMAGE_SIZE_BYTES", 10)

    oversized_b64 = base64.b64encode(b"x" * 100).decode("utf-8")

    event = make_event(body={
        "user_id": "user-1",
        "filename": "big.png",
        "content_type": "image/png",
        "image_base64": oversized_b64,
    })

    response = upload.lambda_handler(event, None)

    assert response["statusCode"] == 400
    assert "exceeds maximum" in json.loads(response["body"])["error"]


def test_upload_malformed_json_body(aws_infra):
    event = make_event(body=None)
    event["body"] = "{not-json"

    response = upload.lambda_handler(event, None)

    assert response["statusCode"] == 400
    assert "valid JSON" in json.loads(response["body"])["error"]


def test_upload_tags_must_be_list(aws_infra):
    event = make_event(body={
        "user_id": "user-1",
        "filename": "cat.png",
        "content_type": "image/png",
        "image_base64": TINY_PNG_BASE64,
        "tags": "not-a-list",
    })

    response = upload.lambda_handler(event, None)

    assert response["statusCode"] == 400
    assert json.loads(response["body"])["error"] == "tags must be a list of strings"
