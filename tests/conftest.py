import base64
import os

import boto3
import pytest
from moto import mock_aws

os.environ.setdefault("AWS_ACCESS_KEY_ID", "testing")
os.environ.setdefault("AWS_SECRET_ACCESS_KEY", "testing")
os.environ.setdefault("AWS_SECURITY_TOKEN", "testing")
os.environ.setdefault("AWS_SESSION_TOKEN", "testing")
os.environ["AWS_REGION"] = "us-east-1"
os.environ["AWS_DEFAULT_REGION"] = "us-east-1"
os.environ["IMAGES_BUCKET"] = "images-bucket-test"
os.environ["IMAGES_TABLE"] = "images-metadata-test"
os.environ["USER_INDEX_NAME"] = "user_id-index"
os.environ.pop("LOCALSTACK_ENDPOINT", None)

TABLE_NAME = os.environ["IMAGES_TABLE"]
BUCKET_NAME = os.environ["IMAGES_BUCKET"]

TINY_PNG_BYTES = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAACklEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="
)

TINY_PNG_BASE64 = base64.b64encode(TINY_PNG_BYTES).decode("utf-8")


@pytest.fixture
def aws_infra():
    with mock_aws():
        s3 = boto3.client("s3", region_name="us-east-1")
        s3.create_bucket(Bucket=BUCKET_NAME)

        ddb = boto3.client("dynamodb", region_name="us-east-1")
        ddb.create_table(
            TableName=TABLE_NAME,
            KeySchema=[
                {"AttributeName": "image_id", "KeyType": "HASH"}
            ],
            AttributeDefinitions=[
                {"AttributeName": "image_id", "AttributeType": "S"},
                {"AttributeName": "user_id", "AttributeType": "S"},
                {"AttributeName": "uploaded_at", "AttributeType": "S"},
            ],
            GlobalSecondaryIndexes=[
                {
                    "IndexName": "user_id-index",
                    "KeySchema": [
                        {"AttributeName": "user_id", "KeyType": "HASH"},
                        {"AttributeName": "uploaded_at", "KeyType": "RANGE"},
                    ],
                    "Projection": {"ProjectionType": "ALL"},
                    "ProvisionedThroughput": {
                        "ReadCapacityUnits": 5,
                        "WriteCapacityUnits": 5,
                    },
                }
            ],
            ProvisionedThroughput={
                "ReadCapacityUnits": 5,
                "WriteCapacityUnits": 5,
            },
        )

        ddb.get_waiter("table_exists").wait(TableName=TABLE_NAME)

        yield


def make_event(
    body=None,
    query_params=None,
    path_params=None,
    is_base64_encoded=False,
):
    import json

    return {
        "body": json.dumps(body) if isinstance(body, dict) else body,
        "queryStringParameters": query_params,
        "pathParameters": path_params,
        "isBase64Encoded": is_base64_encoded,
    }
