import json
import decimal


class DecimalEncoder(json.JSONEncoder):
    """DynamoDB returns Decimal for numbers; make them JSON serialisable."""

    def default(self, o):
        if isinstance(o, decimal.Decimal):
            if o % 1 == 0:
                return int(o)
            return float(o)
        return super().default(o)


CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "Content-Type",
    "Access-Control-Allow-Methods": "GET,POST,DELETE,OPTIONS",
}


def build_response(status_code, body_dict, extra_headers=None, is_binary=False):
    headers = {"Content-Type": "application/json"}
    headers.update(CORS_HEADERS)
    if extra_headers:
        headers.update(extra_headers)

    response = {
        "statusCode": status_code,
        "headers": headers,
    }

    if is_binary:
        response["body"] = body_dict
        response["isBase64Encoded"] = True
    else:
        response["body"] = json.dumps(body_dict, cls=DecimalEncoder)

    return response


def success(body_dict, status_code=200):
    return build_response(status_code, body_dict)


def error(message, status_code=400, details=None):
    body = {"error": message}
    if details:
        body["details"] = details
    return build_response(status_code, body)
