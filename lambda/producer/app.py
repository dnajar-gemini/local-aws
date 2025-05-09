import boto3
import json
import base64
import os
import uuid
import traceback
import sys

# Add the parent directory to sys.path to import the config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    from config import ENDPOINT_URL, REGION, S3_BUCKET_NAME
    print(f"Config loaded successfully: ENDPOINT_URL={ENDPOINT_URL}, REGION={REGION}, S3_BUCKET_NAME={S3_BUCKET_NAME}")
except Exception as e:
    print(f"Error loading config: {str(e)}")
    # Fallback to hardcoded values
    ENDPOINT_URL = "http://localstack:4566"
    REGION = "us-east-2"
    S3_BUCKET_NAME = "pdf-uploads"
    print(f"Using fallback config: ENDPOINT_URL={ENDPOINT_URL}, REGION={REGION}, S3_BUCKET_NAME={S3_BUCKET_NAME}")

# Use localstack instead of localhost for the endpoint URL
try:
    s3 = boto3.client("s3", endpoint_url=ENDPOINT_URL, region_name=REGION)
    # Test S3 connection
    s3.list_buckets()
    print("S3 client initialized successfully")
    
    # Check if bucket exists, create if not
    try:
        s3.head_bucket(Bucket=S3_BUCKET_NAME)
        print(f"Bucket {S3_BUCKET_NAME} exists")
    except:
        print(f"Bucket {S3_BUCKET_NAME} does not exist, creating...")
        try:
            s3.create_bucket(
                Bucket=S3_BUCKET_NAME,
                CreateBucketConfiguration={'LocationConstraint': REGION}
            )
            print(f"Bucket {S3_BUCKET_NAME} created successfully")
        except Exception as e:
            print(f"Error creating bucket: {str(e)}")
except Exception as e:
    print(f"Error initializing S3 client: {str(e)}")
    traceback.print_exc()

def lambda_handler(event, context):
    print("========== PRODUCER FUNCTION INVOKED ==========")
    print(f"Time: {os.environ.get('AWS_LAMBDA_FUNCTION_NAME')} - {uuid.uuid4()}")
    print(f"Event: {json.dumps(event)}")
    print("==============================================")
    
    try:
        # Check if this is a multipart/form-data request by content-type header
        content_type = event.get('headers', {}).get('Content-Type', '') or event.get('headers', {}).get('content-type', '')
        print(f"Content-Type: {content_type}")
        
        if content_type and content_type.startswith('multipart/form-data'):
            print("Processing multipart/form-data request")
            
            try:
                # Get the body, which might be base64 encoded or not
                body = event.get('body', '')
                is_base64 = event.get('isBase64Encoded', False)
                print(f"Body length: {len(body)}, isBase64Encoded: {is_base64}")
                
                # If isBase64Encoded is True, decode it
                if is_base64:
                    try:
                        file_content = base64.b64decode(body)
                        print(f"Decoded base64 content, length: {len(file_content)}")
                    except Exception as e:
                        print(f"Error decoding base64: {str(e)}")
                        traceback.print_exc()
                        raise
                else:
                    # Try to decode anyway - sometimes API Gateway doesn't set the flag correctly
                    try:
                        file_content = base64.b64decode(body)
                        print(f"Decoded base64 content, length: {len(file_content)}")
                    except:
                        # If it's not valid base64, use it as is
                        file_content = body.encode('utf-8') if isinstance(body, str) else body
                        print(f"Using raw content, length: {len(file_content)}")
                
                # Extract filename from Content-Disposition if possible
                # For simplicity, we'll just use a random filename
                file_name = f"uploaded-{uuid.uuid4()}.pdf"
                print(f"Generated filename: {file_name}")
                
                # Upload to S3
                s3_key = file_name
                
                try:
                    response = s3.put_object(
                        Bucket=S3_BUCKET_NAME,
                        Key=s3_key,
                        Body=file_content
                    )
                    print(f"S3 upload successful: {response}")
                except Exception as e:
                    print(f"Error uploading to S3: {str(e)}")
                    traceback.print_exc()
                    raise
                
                return {
                    'statusCode': 200,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*'
                    },
                    'body': json.dumps({
                        'message': 'File uploaded successfully via multipart/form-data',
                        'file_name': file_name,
                        'bucket': S3_BUCKET_NAME,
                        'key': s3_key
                    })
                }
            except Exception as e:
                print(f"Error processing multipart/form-data: {str(e)}")
                traceback.print_exc()
                return {
                    'statusCode': 400,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*'
                    },
                    'body': json.dumps({
                        'message': f'Error processing file upload: {str(e)}'
                    })
                }
    except Exception as e:
        print(f"Error in lambda_handler: {str(e)}")
        traceback.print_exc()
        return {
            'statusCode': 500,
            'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps({
            'message': f'Server error: {str(e)}'
        })
    }