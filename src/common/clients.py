"""
Boto3 client/resource factory.

Works both:
- Inside LocalStack Lambda containers (AWS_ENDPOINT_URL is auto-injected by LocalStack, so plain boto3.client(...) already points at LocalStack).
- When running scripts/tests from host machine against LocalStack, where we rely on LOCALSTACK_ENDPOINT env var (defaults to http://localhost:4566).
- Under moto in unit tests, where AWS_ENDPOINT_URL / LOCALSTACK_ENDPOINT should simply be unset so moto's own mocking takes over.
"""

import os
import boto3

AWS_REGION = os.environ.get("AWS_REGION", "us-east-1")


def _endpoint_url():
    return os.environ.get("LOCALSTACK_ENDPOINT")


def get_client(service_name):
    endpoint_url = _endpoint_url()
    kwargs = {"region_name": AWS_REGION}

    if endpoint_url:
        kwargs["endpoint_url"] = endpoint_url

    return boto3.client(service_name, **kwargs)


def get_resource(service_name):
    endpoint_url = _endpoint_url()
    kwargs = {"region_name": AWS_REGION}

    if endpoint_url:
        kwargs["endpoint_url"] = endpoint_url

    return boto3.resource(service_name, **kwargs)
