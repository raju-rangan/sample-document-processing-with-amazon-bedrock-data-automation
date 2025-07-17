import json
import os
import urllib3
import boto3
from datetime import datetime
from urllib.parse import unquote_plus

# Initialize HTTP client and AWS clients
http = urllib3.PoolManager()
s3_client = boto3.client('s3')

def handler(event, context):
    """
    Lambda function to process S3 document upload events and trigger HTTP webhook
    """
    
    try:
        # Get environment variables
        webhook_url = os.environ.get('WEBHOOK_URL')
        document_bucket = os.environ.get('DOCUMENT_BUCKET')
        
        print(f"Processing S3 event: {json.dumps(event)}")
        
        # Process each S3 record
        for record in event.get('Records', []):
            # Extract S3 event details
            event_name = record.get('eventName')
            s3_info = record.get('s3', {})
            bucket_name = s3_info.get('bucket', {}).get('name')
            object_key = unquote_plus(s3_info.get('object', {}).get('key', ''))
            object_size = s3_info.get('object', {}).get('size', 0)
            
            print(f"Processing: {event_name} for {object_key} in {bucket_name}")
            
            # Validate required data
            if not bucket_name or not object_key:
                print("Missing bucket name or object key")
                continue
            
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
                    'source': 'aws.s3'
                },
                'processing': {
                    'status': 'initiated',
                    'trigger': 'direct_s3_event'
                }
            }
            
            # Send HTTP request to webhook
            if webhook_url and webhook_url != 'https://webhook.site/unique-id-replace-with-actual':
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
                'message': 'Documents processed successfully',
                'processed_count': len(event.get('Records', [])),
                'webhook_status': webhook_status
            })
        }
        
    except Exception as e:
        print(f"Error processing S3 event: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': 'Internal server error',
                'message': str(e)
            })
        }
