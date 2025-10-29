"""Configuration settings for the Mortgage Application Streamlit app."""

import os

# AWS Configuration
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
DYNAMODB_TABLE_NAME = os.getenv("DYNAMODB_TABLE_NAME", "mortgage-applications")
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME", "raw-document-store20250802224425881600000001")

# App Configuration
APP_TITLE = "Mortgage Application Processor"
MAX_FILE_SIZE_MB = 10
ALLOWED_FILE_TYPES = ["pdf"]
