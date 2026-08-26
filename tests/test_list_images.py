import json

from src.handlers import list_images, upload
from tests.conftest import TINY_PNG_BASE64, make_event


def _upload_one(user_id, filename, tags=None, content_type="image/png"):
    event = make_event(body={
        "user_id": user_id,
        "filename": filename,
        "content_type": content_type,
        "image_base64": TINY_PNG_BASE64,
        "tags": tags or [],
    })
    response = upload.lambda_handler(event, None)
    assert response["statusCode"] == 201
    return json.loads(response["body"])


def test_list_all_images(aws_infra):
    _upload_one("user-1", "a.png")
    _upload_one("user-2", "b.png")

    response = list_images.lambda_handler(
        make_event(query_params=None), None
    )

    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert body["count"] == 2


def test_list_filter_by_user_id(aws_infra):
    _upload_one("user-1", "a.png")
    _upload_one("user-1", "b.png")
    _upload_one("user-2", "c.png")

    response = list_images.lambda_handler(
        make_event(query_params={"user_id": "user-1"}), None
    )

    body = json.loads(response["body"])
    assert body["count"] == 2
    assert all(
        item["user_id"] == "user-1"
        for item in body["items"]
    )


def test_list_filter_by_tag(aws_infra):
    _upload_one("user-1", "a.png", tags=["sunset", "beach"])
    _upload_one("user-1", "b.png", tags=["mountain"])

    response = list_images.lambda_handler(
        make_event(query_params={"tag": "sunset"}), None
    )

    body = json.loads(response["body"])
    assert body["count"] == 1
    assert body["items"][0]["filename"] == "a.png"


def test_list_filter_by_user_id_and_tag_combined(aws_infra):
    _upload_one("user-1", "a.png", tags=["sunset"])
    _upload_one("user-1", "b.png", tags=["mountain"])
    _upload_one("user-2", "c.png", tags=["sunset"])

    response = list_images.lambda_handler(
        make_event(
            query_params={
                "user_id": "user-1",
                "tag": "sunset",
            }
        ),
        None,
    )

    body = json.loads(response["body"])
    assert body["count"] == 1
    assert body["items"][0]["filename"] == "a.png"


def test_list_filter_by_content_type(aws_infra):
    _upload_one("user-1", "a.png", content_type="image/png")
    _upload_one("user-1", "b.jpg", content_type="image/jpeg")

    response = list_images.lambda_handler(
        make_event(
            query_params={"content_type": "image/jpeg"}
        ),
        None,
    )

    body = json.loads(response["body"])
    assert body["count"] == 1
    assert body["items"][0]["filename"] == "b.jpg"


def test_list_no_results(aws_infra):
    _upload_one("user-1", "a.png", tags=["sunset"])

    response = list_images.lambda_handler(
        make_event(
            query_params={"tag": "nonexistent-tag"}
        ),
        None,
    )

    body = json.loads(response["body"])
    assert body["count"] == 0
    assert body["items"] == []


def test_list_pagination_limit(aws_infra):
    for i in range(5):
        _upload_one("user-1", f"img-{i}.png")

    response = list_images.lambda_handler(
        make_event(
            query_params={
                "user_id": "user-1",
                "limit": "2",
            }
        ),
        None,
    )

    body = json.loads(response["body"])
    assert body["count"] == 2
    assert body["next_token"] is not None

    response_2 = list_images.lambda_handler(
        make_event(
            query_params={
                "user_id": "user-1",
                "limit": "2",
                "next_token": body["next_token"],
            }
        ),
        None,
    )

    body_2 = json.loads(response_2["body"])
    assert body_2["count"] == 2

    page1_ids = {
        item["image_id"]
        for item in body["items"]
    }

    page2_ids = {
        item["image_id"]
        for item in body_2["items"]
    }

    assert page1_ids.isdisjoint(page2_ids)


def test_list_invalid_limit_rejected(aws_infra):
    for bad in ["0", "not-a-number", "1000"]:
        response = list_images.lambda_handler(
            make_event(
                query_params={"limit": bad}
            ),
            None,
        )

        assert response["statusCode"] == 400
