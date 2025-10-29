"""Data processing utilities for DynamoDB data."""

import pandas as pd
from decimal import Decimal

def parse_dynamodb_item(item):
    """Parse DynamoDB item to Python dict."""
    def parse_value(value):
        if isinstance(value, dict):
            if 'S' in value:
                return value['S']
            elif 'N' in value:
                return float(value['N'])
            elif 'BOOL' in value:
                return value['BOOL']
            elif 'L' in value:
                return [parse_value(v) for v in value['L']]
            elif 'M' in value:
                return {k: parse_value(v) for k, v in value['M'].items()}
        return value
    
    return {k: parse_value(v) for k, v in item.items()}

def format_applications_for_display(applications):
    """Format applications data for display in Streamlit."""
    if not applications:
        return pd.DataFrame()
    
    formatted_data = []
    
    for app in applications:
        parsed_app = parse_dynamodb_item(app)
        
        # Extract key information for display
        row = {
            'Application ID': parsed_app.get('application_id', 'N/A'),
            'Borrower Name': parsed_app.get('borrower_name', 'N/A'),
            'Loan Amount': f"${parsed_app.get('loan_amount', 0):,.2f}",
            'Status': parsed_app.get('status', 'N/A').title(),
            'Created Date': parsed_app.get('created_at', 'N/A')[:10] if parsed_app.get('created_at') else 'N/A',
            'SSN': parsed_app.get('ssn', 'N/A'),
        }
        
        # Add property information if available
        loan_info = parsed_app.get('loan_information', {})
        if isinstance(loan_info, dict) and 'property' in loan_info:
            property_info = loan_info['property']
            if isinstance(property_info, dict):
                row['Property Value'] = f"${property_info.get('value', 0):,.2f}"
                row['Property Address'] = property_info.get('address', 'N/A')
        else:
            row['Property Value'] = 'N/A'
            row['Property Address'] = 'N/A'
        
        formatted_data.append(row)
    
    return pd.DataFrame(formatted_data)

def get_application_details(application):
    """Get detailed information for a specific application."""
    parsed_app = parse_dynamodb_item(application)
    return parsed_app
