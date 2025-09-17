import json
import os
from datetime import datetime, timezone
from decimal import Decimal
from typing import Dict, Any, Optional
from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities.typing import LambdaContext

from model.mortgage_application import MortgageApplication, ApplicationStatus

logger = Logger(service="mortgage-crud-service")

SPEC_S3_URI = os.environ["SPEC_S3_URI"]

MAX_SCAN_LIMIT = 500
DEFAULT_SCAN_LIMIT = 100

@logger.inject_lambda_context(log_event=True)
def lambda_handler(event: Dict[str, Any], context: LambdaContext) -> Dict[str, Any]:
    try:
        if "requestContext" in event and "http" in event["requestContext"]:
            method = event["requestContext"]["http"]["method"]
        else:
            method = event.get("httpMethod", "")
            
        path_params = event.get("pathParameters") or {}
        query_params = event.get("queryStringParameters") or {}
        body = json.loads(event.get("body", {}))
        logger.info(f"Parsed JSON body: {body}")

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
            result = routes[method]()
            if isinstance(result.get("body"), str):
                body_data = json.loads(result["body"])
                result["body"] = json.dumps(body_data, default=str)
            return result

        return response(405, {"error": "Method not allowed"})

    except json.JSONDecodeError:
        return response(400, {"error": "Invalid JSON in request body"})
    except KeyError as e:
        return response(400, {"error": f"Missing required parameter: {str(e)}"})
    except Exception as e:
        logger.exception("Unhandled exception")
        return response(500, {"error": "Internal server error"})


def required_param(params: dict, key: str) -> str:
    if key not in params:
        raise KeyError(key)
    return params[key]


def response(status_code: int, body: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
        },
        "body": json.dumps(body, default=str),
    }


def create_application(data: Dict[str, Any]) -> Dict[str, Any]:
    try:
        application: MortgageApplication = MortgageApplication.create_application(
            **data
        )

        return response(201, {"application_id": application.application_id})

    except Exception as e:
        logger.exception("Error creating application")
        return response(500, {"error": f"Failed to create application: {str(e)}"})


def get_application(app_id: Optional[str]) -> Dict[str, Any]:
    if not app_id:
        return response(400, {"error": "application_id required"})

    try:
        application = MortgageApplication.get(hash_key=app_id)
        
        if not application:
            return response(404, {"error": "Application not found"})

        result = application.to_simple_dict()
        
        return response(200, {"data": result})

    except Exception as e:
        logger.exception("Error retrieving application", extra={"application_id": app_id})
        return response(500, {"error": "Database error"})


def list_applications(params: Dict[str, Any]) -> Dict[str, Any]:
    try:
        page = int(params.get("page", 0))
        limit = min(int(params.get("limit", DEFAULT_SCAN_LIMIT)), MAX_SCAN_LIMIT)
    except ValueError:
        return response(400, {"error": "Invalid limit or page parameters"})

    try:        
        applications = list(MortgageApplication.scan(limit=limit, segment=page))

        items = [app.to_simple_dict() for app in applications]

        response_data = {
            "items": items,
            "page": page,
            "limit": limit,
        }

        return response(200, response_data)

    except Exception as e:
        logger.exception("Error listing applications")
        return response(500, {"error": "Database error"})


def update_application(app_id: Optional[str], data: Dict[str, Any]) -> Dict[str, Any]:
    if not app_id or not isinstance(app_id, str) or not app_id.strip():
        return response(400, {"error": "application_id required and must be a non-empty string"})
    if not data:
        return response(400, {"error": "Update data required"})

    try:
        application = MortgageApplication.get(hash_key=app_id)
        if not application:
            return response(404, {"error": "Application not found"})

        updated_fields = []
        for key, value in data.items():
            if key not in ["application_id", "created_at", "updated_at", "record_version"]:
                if hasattr(application, key):
                    if key == "loan_amount":
                        if not isinstance(value, (int, float)) or value <= 0:
                            return response(400, {"error": "loan_amount must be a positive number"})
                        value = Decimal(str(value))
                    elif key == "status":
                        if not isinstance(value, str):
                            return response(400, {"error": "status must be a string"})
                        value = ApplicationStatus(value)
                    
                    setattr(application, key, value)
                    updated_fields.append(key)

        if updated_fields:
            application.updated_at = datetime.now(timezone.utc)
            application.save()

        result = application.to_simple_dict()
        
        return response(200, {
            "message": "Application updated", 
            "data": result,
            "updated_fields": updated_fields
        })

    except Exception as e:
        logger.exception("Error updating application", extra={"application_id": app_id})
        return response(500, {"error": f"Failed to update application: {str(e)}"})


def delete_application(app_id: Optional[str]) -> Dict[str, Any]:
    if not app_id:
        return response(400, {"error": "application_id required"})

    try:
        application = MortgageApplication.get(hash_key=app_id)
        if not application:
            return response(404, {"error": "Application not found"})

        deleted_data = application.to_simple_dict()

        success = application.delete()
        
        if not success:
            return response(500, {"error": "Failed to delete application"})

        return response(200, {
            "message": "Application deleted", 
            "data": deleted_data
        })

    except Exception as e:
        logger.exception("Error deleting application", extra={"application_id": app_id})
        return response(500, {"error": f"Failed to delete application: {str(e)}"})
