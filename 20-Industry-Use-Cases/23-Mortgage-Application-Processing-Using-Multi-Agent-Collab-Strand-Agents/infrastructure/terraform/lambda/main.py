import json
import uuid
import boto3
import os
import logging
from datetime import datetime, timezone
from decimal import Decimal
from typing import Dict, Any, Optional, Union
from botocore.exceptions import ClientError
from boto3.dynamodb.types import TypeSerializer
from boto3.dynamodb.types import TypeDeserializer
from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities.typing import LambdaContext

logger = Logger(service="mortgage-crud-service")

MAX_SCAN_LIMIT = 500
DEFAULT_SCAN_LIMIT = 100

TABLE_NAME = os.environ["TABLE_NAME"]
dynamodb = boto3.client("dynamodb")

serializer = TypeSerializer()
deserializer = TypeDeserializer()

@logger.inject_lambda_context(log_event=True)
def lambda_handler(event: Dict[str, Any], context: LambdaContext) -> Dict[str, Any]:
    """
    Main Lambda handler for mortgage applications CRUD operations.
    """
    try:
        # Handle both API Gateway v1 and v2 event formats
        if "requestContext" in event and "http" in event["requestContext"]:
            # API Gateway v2 format
            method = event["requestContext"]["http"]["method"]
        else:
            # API Gateway v1 format (fallback)
            method = event.get("httpMethod", "")
            
        path_params = event.get("pathParameters") or {}
        query_params = event.get("queryStringParameters") or {}
        body = parse_body(event.get("body"))

        routes = {
            "POST": lambda: create_application(body),
            "GET": lambda: (
                get_application(path_params["application_id"])
                if "application_id" in path_params
                else list_applications(query_params)
            ),
            "PUT": lambda: update_application(required_param(path_params, "application_id"), body),
            "DELETE": lambda: delete_application(required_param(path_params, "application_id")),
        }

        if method in routes:
            return routes[method]()

        return response(405, {"error": "Method not allowed"})

    except json.JSONDecodeError:
        return response(400, {"error": "Invalid JSON in request body"})
    except KeyError as e:
        return response(400, {"error": f"Missing required parameter: {str(e)}"})
    except Exception as e:
        logger.exception("Unhandled exception")
        return response(500, {"error": "Internal server error"})


def parse_body(raw_body: Optional[Union[str, dict]]) -> dict:
    """Parse JSON body safely."""
    if not raw_body:
        return {}
    if isinstance(raw_body, str):
        return json.loads(raw_body)
    return raw_body


def required_param(params: dict, key: str) -> str:
    """Ensure a required path param exists."""
    if key not in params:
        raise KeyError(key)
    return params[key]

def validate_required(data: Dict[str, Any], fields: list) -> list:
    """Return a list of missing required fields."""
    return [f for f in fields if not data.get(f)]

def response(status_code: int, body: Dict[str, Any]) -> Dict[str, Any]:
    """Standard API Gateway response with CORS headers."""
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
        },
        "body": json.dumps(body, default=decimal_default),
    }


def decimal_default(obj: Any) -> Union[float, str]:
    """Serialize DynamoDB Decimal to float."""
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")


def to_decimal_if_number(value: Any) -> Any:
    """Convert to Decimal if numeric."""
    if isinstance(value, (int, float, str)) and str(value).replace(".", "", 1).isdigit():
        return Decimal(str(value))
    return value


def create_application(data: Dict[str, Any]) -> Dict[str, Any]:
    missing_fields = validate_required(data, ["borrower_name", "status", "application_date"])
    if missing_fields:
        return response(400, {"error": f"Missing required fields: {missing_fields}"})

    application_id = str(uuid.uuid4())
    timestamp = datetime.now(timezone.utc).isoformat()

    item = {
        **data,
        "application_id": application_id,
        "created_at": timestamp,
        "updated_at": timestamp,
    }

    if "loan_amount" in item and isinstance(item["loan_amount"], (int, float)):
        item["loan_amount"] = Decimal(str(item["loan_amount"]))

    item_serialized = {k: serializer.serialize(v) for k, v in item.items()}

    try:
        dynamodb.put_item(
            TableName=TABLE_NAME,
            Item=item_serialized,
            ConditionExpression="attribute_not_exists(application_id)"
        )
        return response(201, {"message": "Application created", "data": item})

    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        if error_code == "ConditionalCheckFailedException":
            return response(409, {"error": "Application ID already exists"})

        logger.exception("DynamoDB put_item error", extra={"application_id": data.get("application_id")})
        return response(500, {"error": "Database error"})


def get_application(app_id: Optional[str]) -> Dict[str, Any]:
    if not app_id:
        return response(400, {"error": "application_id required"})

    try:
        result = dynamodb.get_item(
            TableName=TABLE_NAME,
            Key={"application_id": {"S": app_id}}
        )

        if "Item" not in result:
            return response(404, {"error": "Application not found"})

        item = {k: deserializer.deserialize(v) for k, v in result["Item"].items()}

        return response(200, {"data": item})

    except ClientError:
        logger.exception("DynamoDB get_item error", extra={"application_id": app_id})
        return response(500, {"error": "Database error"})


def list_applications(params: Dict[str, Any]) -> Dict[str, Any]:
    try:
        limit = min(int(params.get("limit", DEFAULT_SCAN_LIMIT)), MAX_SCAN_LIMIT)
    except ValueError:
        return response(400, {"error": "Invalid limit parameter"})

    scan_kwargs = {"TableName": TABLE_NAME, "Limit": limit}

    if params.get("last_evaluated_key"):
        try:
            lek_raw = json.loads(params["last_evaluated_key"])
            lek = {k: serializer.serialize(v) for k, v in lek_raw.items()}
            scan_kwargs["ExclusiveStartKey"] = lek
        except (json.JSONDecodeError, TypeError):
            return response(400, {"error": "Invalid last_evaluated_key format"})

    try:
        result = dynamodb.scan(**scan_kwargs)

        items = [
            {k: deserializer.deserialize(v) for k, v in item.items()}
            for item in result.get("Items", [])
        ]

        response_data = {
            "data": items,
            "count": len(items),
            "has_more": "LastEvaluatedKey" in result,
        }

        if result.get("LastEvaluatedKey"):
            lek_deserialized = {
                k: deserializer.deserialize(v) for k, v in result["LastEvaluatedKey"].items()
            }
            response_data["last_evaluated_key"] = json.dumps(lek_deserialized)

        return response(200, response_data)

    except ClientError:
        logger.exception("DynamoDB scan error")
        return response(500, {"error": "Database error"})


def update_application(app_id: Optional[str], data: Dict[str, Any]) -> Dict[str, Any]:
    if not app_id:
        return response(400, {"error": "application_id required"})
    if not data:
        return response(400, {"error": "Update data required"})

    # Always update updated_at
    update_expr = ["updated_at = :updated_at"]
    attr_values = {":updated_at": serializer.serialize(datetime.now(timezone.utc).isoformat())}
    attr_names = {}

    for key, value in data.items():
        if key != "application_id":
            safe_key = f"#{key}"
            value_key = f":{key}"
            update_expr.append(f"{safe_key} = {value_key}")
            attr_names[safe_key] = key

            # Convert numbers to Decimal
            if key == "loan_amount" and isinstance(value, (int, float)):
                value = Decimal(str(value))
            attr_values[value_key] = serializer.serialize(value)

    try:
        result = dynamodb.update_item(
            TableName=TABLE_NAME,
            Key={"application_id": {"S": app_id}},
            UpdateExpression="SET " + ", ".join(update_expr),
            ExpressionAttributeNames=attr_names,
            ExpressionAttributeValues=attr_values,
            ConditionExpression="attribute_exists(application_id)",
            ReturnValues="ALL_NEW",
        )

        # Deserialize updated item
        updated_item = {
            k: deserializer.deserialize(v) for k, v in result.get("Attributes", {}).items()
        }

        return response(
            200, {"message": "Application updated", "data": updated_item}
        )

    except ClientError as e:
        code = e.response["Error"]["Code"]
        if code == "ConditionalCheckFailedException":
            return response(404, {"error": "Application not found"})

        logger.exception("DynamoDB update_item error", extra={"application_id": app_id})
        return response(500, {"error": "Database error"})


def delete_application(app_id: Optional[str]) -> Dict[str, Any]:
    if not app_id:
        return response(400, {"error": "application_id required"})

    try:
        result = dynamodb.delete_item(
            TableName=TABLE_NAME,
            Key={"application_id": {"S": app_id}},
            ConditionExpression="attribute_exists(application_id)",
            ReturnValues="ALL_OLD",
        )

        if "Attributes" not in result:
            return response(404, {"error": "Application not found"})

        deleted_item = {k: deserializer.deserialize(v) for k, v in result["Attributes"].items()}

        return response(
            200, {"message": "Application deleted", "data": deleted_item}
        )

    except ClientError as e:
        code = e.response["Error"]["Code"]
        if code == "ConditionalCheckFailedException":
            return response(404, {"error": "Application not found"})

        logger.exception("DynamoDB delete_item error", extra={"application_id": app_id})
        return response(500, {"error": "Database error"})