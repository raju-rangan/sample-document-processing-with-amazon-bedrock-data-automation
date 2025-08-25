import json
import os
import logging
from datetime import datetime, timezone
from decimal import Decimal
from typing import Dict, Any, Optional, Union
from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities.typing import LambdaContext

# Import our optimized mortgage application model
from mortgage_application import MortgageApplication, ApplicationStatus

logger = Logger(service="mortgage-crud-service")

MAX_SCAN_LIMIT = 500
DEFAULT_SCAN_LIMIT = 100

@logger.inject_lambda_context(log_event=True)
def lambda_handler(event: Dict[str, Any], context: LambdaContext) -> Dict[str, Any]:
    """
    Main Lambda handler for mortgage applications CRUD operations.
    Now using optimized MortgageApplication model with enhanced query capabilities.
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
            result = routes[method]()
            # Add model version info to response
            if isinstance(result.get("body"), str):
                body_data = json.loads(result["body"])
                body_data["model_version"] = "optimized_v1"
                result["body"] = json.dumps(body_data, default=decimal_default)
            return result

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



def create_application(data: Dict[str, Any]) -> Dict[str, Any]:
    """Create a new mortgage application using the optimized model."""
    try:
        # Validate required fields for application creation
        required_fields = ["borrower_name", "ssn", "loan_amount", "loan_originator_id", "property_state", "configuration"]
        missing_fields = validate_required(data, required_fields)
        if missing_fields:
            return response(400, {"error": f"Missing required fields: {missing_fields}"})

        # Extract and validate required fields with proper type checking
        borrower_name = data.get("borrower_name")
        if not isinstance(borrower_name, str) or not borrower_name.strip():
            return response(400, {"error": "borrower_name must be a non-empty string"})

        ssn = data.get("ssn")
        if not isinstance(ssn, str) or not ssn.strip():
            return response(400, {"error": "ssn must be a non-empty string"})

        loan_amount = data.get("loan_amount")
        if not isinstance(loan_amount, (int, float)) or loan_amount <= 0:
            return response(400, {"error": "loan_amount must be a positive number"})

        loan_originator_id = data.get("loan_originator_id")
        if not isinstance(loan_originator_id, str) or not loan_originator_id.strip():
            return response(400, {"error": "loan_originator_id must be a non-empty string"})

        property_state = data.get("property_state")
        if not isinstance(property_state, str) or not property_state.strip():
            return response(400, {"error": "property_state must be a non-empty string"})

        configuration_data = data.get("configuration")
        if not isinstance(configuration_data, dict):
            return response(400, {"error": "Configuration must be a valid object"})

        # Validate that configuration has required sections
        required_config_sections = [
            'personal_information',
            'employment_information', 
            'assets',
            'liabilities',
            'loan_information',
            'loan_originator_information',
            'declarations'
        ]
        
        missing_config_sections = [section for section in required_config_sections 
                                 if section not in configuration_data]
        if missing_config_sections:
            return response(400, {
                "error": f"Configuration missing required sections: {missing_config_sections}",
                "required_sections": required_config_sections
            })

        # Extract optional fields with type checking
        application_date = data.get("application_date")
        if application_date is not None and not isinstance(application_date, str):
            return response(400, {"error": "application_date must be a string if provided"})

        description = data.get("description")
        if description is not None and not isinstance(description, str):
            return response(400, {"error": "description must be a string if provided"})

        # Create application using optimized model
        application = MortgageApplication.create_application(
            borrower_name=borrower_name,
            ssn=ssn,
            loan_amount=loan_amount,
            loan_originator_id=loan_originator_id,
            property_state=property_state,
            configuration_data=configuration_data,
            application_date=application_date,
            description=description
        )

        # Convert to dict for response
        result = application.to_dict()
        
        return response(201, {"message": "Application created", "data": result})

    except Exception as e:
        logger.exception("Error creating application")
        return response(500, {"error": f"Failed to create application: {str(e)}"})





def get_application(app_id: Optional[str]) -> Dict[str, Any]:
    """Get a mortgage application by ID using the optimized model."""
    if not app_id:
        return response(400, {"error": "application_id required"})

    try:
        # Use the optimized model's safe get method
        application = MortgageApplication.get_application_safely(app_id)
        
        if not application:
            return response(404, {"error": "Application not found"})

        # Convert to dict for response
        result = application.to_dict()
        
        return response(200, {"data": result})

    except Exception as e:
        logger.exception("Error retrieving application", extra={"application_id": app_id})
        return response(500, {"error": "Database error"})





def list_applications(params: Dict[str, Any]) -> Dict[str, Any]:
    """List mortgage applications with enhanced query capabilities using the optimized model."""
    try:
        limit = min(int(params.get("limit", DEFAULT_SCAN_LIMIT)), MAX_SCAN_LIMIT)
    except ValueError:
        return response(400, {"error": "Invalid limit parameter"})

    try:
        # Check for specific query parameters to use optimized indexes
        status = params.get("status")
        borrower_name = params.get("borrower_name")
        loan_originator_id = params.get("loan_originator_id")
        property_state = params.get("property_state")
        min_amount = params.get("min_amount")
        max_amount = params.get("max_amount")
        
        applications = []
        
        # Use appropriate index-based query if parameters are provided
        if status:
            try:
                status_enum = ApplicationStatus(status)
                if min_amount or max_amount:
                    # Use loan amount index for amount-based queries
                    applications = MortgageApplication.get_by_amount_range(
                        status_enum,
                        min_amount=float(min_amount) if min_amount else None,
                        max_amount=float(max_amount) if max_amount else None,
                        limit=limit
                    )
                else:
                    # Use status index
                    applications = MortgageApplication.get_by_status(status_enum, limit=limit)
            except ValueError:
                return response(400, {"error": f"Invalid status: {status}"})
                
        elif borrower_name:
            # Use borrower name index
            applications = MortgageApplication.get_by_borrower_name(borrower_name, limit=limit)
            
        elif loan_originator_id:
            # Use loan originator index
            applications = MortgageApplication.get_by_originator(loan_originator_id, limit=limit)
            
        elif property_state:
            # Use property state index
            applications = MortgageApplication.get_by_state_and_amount_range(
                property_state,
                min_amount=float(min_amount) if min_amount else None,
                max_amount=float(max_amount) if max_amount else None,
                limit=limit
            )
        else:
            # Fall back to scan operation for general listing
            # Use the model's scan method for general queries
            applications = list(MortgageApplication.scan(limit=limit))

        # Convert applications to dict format
        items = [app.to_dict() for app in applications]

        response_data = {
            "data": items,
            "count": len(items),
            "has_more": len(items) >= limit,  # Simple approximation
            "query_type": "index_query"  # Indicate this used an optimized query
        }

        return response(200, response_data)

    except Exception as e:
        logger.exception("Error listing applications")
        return response(500, {"error": "Database error"})





def update_application(app_id: Optional[str], data: Dict[str, Any]) -> Dict[str, Any]:
    """Update a mortgage application using the optimized model."""
    if not app_id or not isinstance(app_id, str) or not app_id.strip():
        return response(400, {"error": "application_id required and must be a non-empty string"})
    if not data:
        return response(400, {"error": "Update data required"})

    try:
        # Get the existing application
        application = MortgageApplication.get_application_safely(app_id)
        if not application:
            return response(404, {"error": "Application not found"})

        # Handle status updates using the optimized method
        if "status" in data:
            status_value = data["status"]
            if not isinstance(status_value, str):
                return response(400, {"error": "status must be a string"})
            
            try:
                new_status = ApplicationStatus(status_value)
                application.update_status(new_status)
                # Remove status from data since it's already handled
                data = {k: v for k, v in data.items() if k != "status"}
            except ValueError:
                return response(400, {"error": f"Invalid status: {status_value}"})

        # Update other fields directly on the model
        updated_fields = []
        for key, value in data.items():
            if key not in ["application_id", "created_at", "record_version"]:  # Skip read-only fields
                if hasattr(application, key):
                    # Convert loan_amount to Decimal if needed
                    if key == "loan_amount":
                        if not isinstance(value, (int, float)) or value <= 0:
                            return response(400, {"error": "loan_amount must be a positive number"})
                        value = Decimal(str(value))
                    elif key in ["borrower_name", "ssn", "loan_originator_id", "property_state", "description"]:
                        if value is not None and (not isinstance(value, str) or not str(value).strip()):
                            return response(400, {"error": f"{key} must be a non-empty string if provided"})
                    
                    setattr(application, key, value)
                    updated_fields.append(key)

        # Save the updated application if there were changes
        if updated_fields or "status" in data:
            application.updated_at = datetime.now(timezone.utc)
            application.save()

        # Convert to dict for response
        result = application.to_dict()
        
        return response(200, {
            "message": "Application updated", 
            "data": result,
            "updated_fields": updated_fields
        })

    except Exception as e:
        logger.exception("Error updating application", extra={"application_id": app_id})
        return response(500, {"error": f"Failed to update application: {str(e)}"})





def delete_application(app_id: Optional[str]) -> Dict[str, Any]:
    """Delete a mortgage application using the optimized model."""
    if not app_id:
        return response(400, {"error": "application_id required"})

    try:
        # Get the existing application first
        application = MortgageApplication.get_application_safely(app_id)
        if not application:
            return response(404, {"error": "Application not found"})

        # Convert to dict before deletion for response
        deleted_data = application.to_dict()

        # Delete using the optimized model's safe delete method
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


