"""AWS utilities for S3 and DynamoDB operations."""

import boto3
import uuid
from datetime import datetime
from config import AWS_REGION, S3_BUCKET_NAME, DYNAMODB_TABLE_NAME

def get_s3_client():
    """Get S3 client."""
    return boto3.client('s3', region_name=AWS_REGION)

def get_dynamodb_client():
    """Get DynamoDB client."""
    return boto3.client('dynamodb', region_name=AWS_REGION)

def upload_file_to_s3(file_content, filename):
    """Upload file to S3 bucket."""
    try:
        s3_client = get_s3_client()
        
        # Generate unique key for the file
        file_key = f"uploads/{datetime.now().strftime('%Y/%m/%d')}/{uuid.uuid4()}_{filename}"
        
        # Upload file
        s3_client.put_object(
            Bucket=S3_BUCKET_NAME,
            Key=file_key,
            Body=file_content,
            ContentType='application/pdf'
        )
        
        return file_key
    except Exception as e:
        raise Exception(f"Failed to upload file to S3: {str(e)}")

def get_all_applications():
    """Get all mortgage applications from DynamoDB."""
    try:
        dynamodb = get_dynamodb_client()
        
        response = dynamodb.scan(
            TableName=DYNAMODB_TABLE_NAME
        )
        
        return response.get('Items', [])
    except Exception as e:
        raise Exception(f"Failed to fetch applications: {str(e)}")
