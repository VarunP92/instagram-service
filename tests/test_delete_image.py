import json

from src.common import db
from src.handlers import delete_image, get_image, upload
from tests.conftest import TINY_PNG_BASE64, make_event


def _upload_one(user_id="user-1"):
    event = make_event(body={
        "user_id": user_id,
        "filename": "cat.png",
        "content_type": "image/png",
        "image_base64": TINY_PNG_BASE64,
    })

    return json.loads(
        upload.lambda_handler(event, None)["body"]
    )


def test_delete_image_success(aws_infra):
    created = _upload_one()

    response = delete_image.lambda_handler(
        make_event(
            path_params={
                "image_id": created["image_id"]
            }
        ),
        None,
    )

    assert response["statusCode"] == 200
    assert db.get_image_metadata(
        created["image_id"]
    ) is None

    get_response = get_image.lambda_handler(
        make_event(
            path_params={
                "image_id": created["image_id"]
            }
        ),
        None,
    )

    assert get_response["statusCode"] == 404


def test_delete_image_not_found(aws_infra):
    response = delete_image.lambda_handler(
        make_event(
            path_params={
                "image_id": "does-not-exist"
            }
        ),
        None,
    )

    assert response["statusCode"] == 404


def test_delete_image_wrong_owner_forbidden(aws_infra):
    created = _upload_one(user_id="user-1")

    response = delete_image.lambda_handler(
        make_event(
            path_params={
                "image_id": created["image_id"]
            },
            query_params={
                "user_id": "user-2"
            },
        ),
        None,
    )

    assert response["statusCode"] == 403

    assert db.get_image_metadata(
        created["image_id"]
    ) is not None


def test_delete_image_correct_owner_allowed(aws_infra):
    created = _upload_one(user_id="user-1")

    response = delete_image.lambda_handler(
        make_event(
            path_params={
                "image_id": created["image_id"]
            },
            query_params={
                "user_id": "user-1"
            },
        ),
        None,
    )

    assert response["statusCode"] == 200


def test_delete_image_missing_path_param(aws_infra):
    response = delete_image.lambda_handler(
        make_event(path_params=None),
        None,
    )

    assert response["statusCode"] == 400
