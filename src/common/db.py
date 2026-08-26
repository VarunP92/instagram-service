import base64
import json
import os

from boto3.dynamodb.conditions import Attr, Key

from src.common.clients import get_resource

TABLE_NAME = os.environ.get("IMAGES_TABLE", "images-metadata")
USER_INDEX_NAME = os.environ.get("USER_INDEX_NAME", "user_id-index")


def _table():
    return get_resource("dynamodb").Table(TABLE_NAME)


def put_image_metadata(item):
    _table().put_item(Item=item)
    return item


def get_image_metadata(image_id):
    resp = _table().get_item(Key={"image_id": image_id})
    return resp.get("Item")


def delete_image_metadata(image_id):
    _table().delete_item(Key={"image_id": image_id})


def _encode_token(last_evaluated_key):
    if not last_evaluated_key:
        return None
    raw = json.dumps(last_evaluated_key).encode("utf-8")
    return base64.urlsafe_b64encode(raw).decode("utf-8")


def _decode_token(token):
    if not token:
        return None
    try:
        raw = base64.urlsafe_b64decode(token.encode("utf-8"))
        return json.loads(raw)
    except Exception:
        return None


def _build_filter_expression(
    tag=None,
    content_type=None,
    start_date=None,
    end_date=None,
):
    filters = []

    if tag:
        filters.append(Attr("tags").contains(tag))

    if content_type:
        filters.append(Attr("content_type").eq(content_type))

    if start_date:
        filters.append(Attr("uploaded_at").gte(start_date))

    if end_date:
        filters.append(Attr("uploaded_at").lte(end_date))

    combined = None

    for condition in filters:
        combined = condition if combined is None else combined & condition

    return combined


def list_images(
    user_id=None,
    tag=None,
    content_type=None,
    start_date=None,
    end_date=None,
    limit=20,
    next_token=None,
):
    table = _table()

    exclusive_start_key = _decode_token(next_token)

    filter_expression = _build_filter_expression(
        tag=tag,
        content_type=content_type,
        start_date=start_date,
        end_date=end_date,
    )

    kwargs = {"Limit": limit}

    if exclusive_start_key:
        kwargs["ExclusiveStartKey"] = exclusive_start_key

    if user_id:
        kwargs["IndexName"] = USER_INDEX_NAME
        kwargs["KeyConditionExpression"] = Key("user_id").eq(user_id)

        if filter_expression is not None:
            kwargs["FilterExpression"] = filter_expression

        response = table.query(**kwargs)

    else:
        if filter_expression is not None:
            kwargs["FilterExpression"] = filter_expression

        response = table.scan(**kwargs)

    items = response.get("Items", [])
    new_token = _encode_token(response.get("LastEvaluatedKey"))

    return items, new_token
