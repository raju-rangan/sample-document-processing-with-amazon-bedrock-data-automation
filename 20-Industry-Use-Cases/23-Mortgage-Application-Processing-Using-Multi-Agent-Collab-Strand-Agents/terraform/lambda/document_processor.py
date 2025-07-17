import json
import os
import urllib3
import boto3
from datetime import datetime

# Initialize HTTP client and AWS clients
http = urllib3.PoolManager()
s3_client = boto3.client('s3')

def handler(event, context):
    """
    Lambda function to process document upload events and trigger HTTP webhook
    """
    
    try:
        # Get environment variables
        webhook_url = os.environ.get('WEBHOOK_URL')
        vector_bucket = os.environ.get('VECTOR_BUCKET')
        document_bucket = os.environ.get('DOCUMENT_BUCKET')
        
        print(f"Processing event: {json.dumps(event)}")
        
        # Extract S3 event details from EventBridge event
        if 'detail' in event:
            detail = event['detail']
            bucket_name = detail.get('bucket', {}).get('name')
            object_key = detail.get('object', {}).get('key')
            object_size = detail.get('object', {}).get('size', 0)
            event_name = detail.get('eventName')
        else:
            print("No detail found in event")
            return {
                'statusCode': 400,
                'body': json.dumps('Invalid event format')
            }
        
        # Validate required data
        if not bucket_name or not object_key:
            print("Missing bucket name or object key")
            return {
                'statusCode': 400,
                'body': json.dumps('Missing required S3 event data')
            }
        
        # Get object metadata
        try:
            response = s3_client.head_object(Bucket=bucket_name, Key=object_key)
            content_type = response.get('ContentType', 'unknown')
            last_modified = response.get('LastModified')
        except Exception as e:
            print(f"Error getting object metadata: {str(e)}")
            content_type = 'unknown'
            last_modified = None
        
        # Prepare webhook payload
        webhook_payload = {
            'event_type': 'document_uploaded',
            'timestamp': datetime.utcnow().isoformat(),
            'document': {
                'bucket': bucket_name,
                'key': object_key,
                'size': object_size,
                'content_type': content_type,
                'last_modified': last_modified.isoformat() if last_modified else None
            },
            's3_event': {
                'event_name': event_name,
                'source': event.get('source', 'aws.s3')
            },
            'processing': {
                'vector_bucket': vector_bucket,
                'status': 'initiated'
            }
        }
        
        # Send HTTP request to webhook
        if webhook_url and webhook_url != 'https://webhook.site/unique-id':
            try:
                encoded_data = json.dumps(webhook_payload).encode('utf-8')
                
                response = http.request(
                    'POST',
                    webhook_url,
                    body=encoded_data,
                    headers={
                        'Content-Type': 'application/json',
                        'User-Agent': 'AWS-Lambda-Document-Processor/1.0'
                    },
                    timeout=30
                )
                
                print(f"Webhook response status: {response.status}")
                print(f"Webhook response data: {response.data.decode('utf-8')}")
                
                webhook_status = 'success' if response.status < 400 else 'failed'
                
            except Exception as e:
                print(f"Error calling webhook: {str(e)}")
                webhook_status = 'failed'
        else:
            print("No valid webhook URL configured, skipping HTTP request")
            webhook_status = 'skipped'
        
        # Log processing completion
        print(f"Document processing completed for {object_key}")
        print(f"Webhook status: {webhook_status}")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Document processed successfully',
                'document': object_key,
                'webhook_status': webhook_status,
                'payload': webhook_payload
            })
        }
        
    except Exception as e:
        print(f"Error processing document: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': 'Internal server error',
                'message': str(e)
            })
        }
