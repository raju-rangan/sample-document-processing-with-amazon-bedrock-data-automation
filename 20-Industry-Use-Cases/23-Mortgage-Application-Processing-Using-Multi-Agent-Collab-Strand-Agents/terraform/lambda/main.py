import json
import boto3
import os
import logging
from datetime import datetime, timezone
from decimal import Decimal
from typing import Dict, Any, Optional, Union
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

MAX_SCAN_LIMIT = 500
DEFAULT_SCAN_LIMIT = 100

TABLE_NAME = os.environ.get("TABLE_NAME")
if not TABLE_NAME:
    raise RuntimeError("Missing required environment variable: TABLE_NAME")

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(TABLE_NAME) 


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Main Lambda handler for mortgage applications CRUD operations.
    """
    try:
        logger.info(f"Incoming event: {json.dumps(event)}")

        method = event.get("httpMethod")
        path_params = event.get("pathParameters") or {}
        query_params = event.get("queryStringParameters") or {}
        body = {}
        if event.get("body"):
            if isinstance(event["body"], str):
                body = json.loads(event["body"])
            else:
                body = event["body"]

        if method == "POST":
            return create_application(body)
        elif method == "GET":
            app_id = path_params.get("application_id")
            return get_application(app_id) if app_id else list_applications(query_params)
        elif method == "PUT":
            return update_application(path_params.get("application_id"), body)
        elif method == "DELETE":
            return delete_application(path_params.get("application_id"))
        else:
            return response(405, {"error": "Method not allowed"})

    except json.JSONDecodeError:
        return response(400, {"error": "Invalid JSON in request body"})
    except Exception as e:
        logger.exception("Unhandled exception")
        return response(500, {"error": "Internal server error"})


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
    required = ["application_id", "borrower_name", "status", "application_date"]
    missing = [f for f in required if not data.get(f)]
    if missing:
        return response(400, {"error": f"Missing required fields: {missing}"})

    item = {
        **data,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }

    if "loan_amount" in item:
        item["loan_amount"] = to_decimal_if_number(item["loan_amount"])

    try:
        table.put_item(
            Item=item,
            ConditionExpression="attribute_not_exists(application_id)",
        )
        return response(201, {"message": "Application created", "data": item})
    except ClientError as e:
        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            return response(409, {"error": "Application ID already exists"})
        logger.exception("DynamoDB put_item error")
        return response(500, {"error": "Database error"})


def get_application(app_id: Optional[str]) -> Dict[str, Any]:
    if not app_id:
        return response(400, {"error": "application_id required"})

    try:
        result = table.get_item(Key={"application_id": app_id})
        if "Item" not in result:
            return response(404, {"error": "Application not found"})
        return response(200, {"data": result["Item"]})
    except ClientError:
        logger.exception("DynamoDB get_item error")
        return response(500, {"error": "Database error"})


def list_applications(params: Dict[str, Any]) -> Dict[str, Any]:
    try:
        limit = min(int(params.get("limit", DEFAULT_SCAN_LIMIT)), MAX_SCAN_LIMIT)
    except ValueError:
        return response(400, {"error": "Invalid limit parameter"})

    scan_kwargs = {"Limit": limit}

    if params.get("last_evaluated_key"):
        try:
            scan_kwargs["ExclusiveStartKey"] = json.loads(params["last_evaluated_key"])
        except json.JSONDecodeError:
            return response(400, {"error": "Invalid last_evaluated_key format"})

    try:
        result = table.scan(**scan_kwargs)
        response_data = {
            "data": result.get("Items", []),
            "count": len(result.get("Items", [])),
            "has_more": "LastEvaluatedKey" in result,
        }

        if result.get("LastEvaluatedKey"):
            response_data["last_evaluated_key"] = json.dumps(
                result["LastEvaluatedKey"], default=decimal_default
            )

        return response(200, response_data)
    except ClientError:
        logger.exception("DynamoDB scan error")
        return response(500, {"error": "Database error"})


def update_application(app_id: Optional[str], data: Dict[str, Any]) -> Dict[str, Any]:
    if not app_id:
        return response(400, {"error": "application_id required"})
    if not data:
        return response(400, {"error": "Update data required"})

    update_expr = ["updated_at = :updated_at"]
    attr_values = {":updated_at": datetime.now(timezone.utc).isoformat()}
    attr_names = {}

    for key, value in data.items():
        if key != "application_id":
            safe_key = f"#{key}"
            value_key = f":{key}"
            update_expr.append(f"{safe_key} = {value_key}")
            attr_names[safe_key] = key
            attr_values[value_key] = (
                to_decimal_if_number(value) if key == "loan_amount" else value
            )

    try:
        result = table.update_item(
            Key={"application_id": app_id},
            UpdateExpression="SET " + ", ".join(update_expr),
            ExpressionAttributeNames=attr_names,
            ExpressionAttributeValues=attr_values,
            ConditionExpression="attribute_exists(application_id)",
            ReturnValues="ALL_NEW",
        )
        return response(
            200, {"message": "Application updated", "data": result.get("Attributes")}
        )
    except ClientError as e:
        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            return response(404, {"error": "Application not found"})
        logger.exception("DynamoDB update_item error")
        return response(500, {"error": "Database error"})


def delete_application(app_id: Optional[str]) -> Dict[str, Any]:
    if not app_id:
        return response(400, {"error": "application_id required"})

    try:
        result = table.delete_item(
            Key={"application_id": app_id},
            ConditionExpression="attribute_exists(application_id)",
            ReturnValues="ALL_OLD",
        )
        if "Attributes" not in result:
            return response(404, {"error": "Application not found"})
        return response(
            200, {"message": "Application deleted", "data": result["Attributes"]}
        )
    except ClientError as e:
        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            return response(404, {"error": "Application not found"})
        logger.exception("DynamoDB delete_item error")
        return response(500, {"error": "Database error"})