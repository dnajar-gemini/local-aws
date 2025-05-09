import boto3
import json
import os
import hashlib
import traceback
import sys

# Add the parent directory to sys.path to import the config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    from config import ENDPOINT_URL, REGION, SQS_QUEUE_A
    print(f"Config loaded successfully: ENDPOINT_URL={ENDPOINT_URL}, REGION={REGION}, SQS_QUEUE_A={SQS_QUEUE_A}")
except Exception as e:
    print(f"Error loading config: {str(e)}")
    # Fallback to hardcoded values
    ENDPOINT_URL = "http://localstack:4566"
    REGION = "us-east-2"
    SQS_QUEUE_A = "queue-a"
    print(f"Using fallback config: ENDPOINT_URL={ENDPOINT_URL}, REGION={REGION}, SQS_QUEUE_A={SQS_QUEUE_A}")

# Initialize AWS clients with the endpoint URL for LocalStack
try:
    s3 = boto3.client("s3", endpoint_url=ENDPOINT_URL, region_name=REGION)
    sqs = boto3.client("sqs", endpoint_url=ENDPOINT_URL, region_name=REGION)
    print("AWS clients initialized successfully")
except Exception as e:
    print(f"Error initializing AWS clients: {str(e)}")
    traceback.print_exc()

# Get the SQS queue URL
queue_url = f"{ENDPOINT_URL}/000000000000/{SQS_QUEUE_A}"
download_path = "/tmp/downloaded.pdf"

def lambda_handler(event, context):
    print("========== PDF LISTENER FUNCTION INVOKED ==========")
    print(f"Event: {json.dumps(event)}")
    print("=================================================")
    
    for record in event["Records"]:
        try:
            # Extract bucket and key from the S3 event
            bucket = record["s3"]["bucket"]["name"]
            key = record["s3"]["object"]["key"]
            
            print(f"Processing file: {key} from bucket: {bucket}")
            
            try:
                # Download the file from S3
                s3.download_file(bucket, key, download_path)
                print(f"File downloaded successfully to {download_path}")
            except Exception as e:
                print(f"Error downloading file: {str(e)}")
                traceback.print_exc()
                continue
            
            try:
                # Get file size
                file_size = os.path.getsize(download_path)
                print(f"File size: {file_size} bytes")
                
                # Calculate a simple signature (MD5 hash of the file)
                with open(download_path, 'rb') as f:
                    file_content = f.read()
                    file_signature = hashlib.md5(file_content).hexdigest()
                
                print(f"File signature: {file_signature}")
            except Exception as e:
                print(f"Error processing file metadata: {str(e)}")
                traceback.print_exc()
                continue
            
            try:
                # Send a message to SQS queue-a
                message = {
                    "bucket": bucket,
                    "key": key,
                    "size": file_size,
                    "signature": file_signature,
                    "source": "pdf_listener"
                }
                
                response = sqs.send_message(QueueUrl=queue_url, MessageBody=json.dumps(message))
                print(f"Message sent to SQS queue-a: {response}")
            except Exception as e:
                print(f"Error sending message to SQS: {str(e)}")
                traceback.print_exc()
                continue
            
        except Exception as e:
            print(f"Error processing record: {str(e)}")
            traceback.print_exc()
            continue
    
    return {
        'statusCode': 200,
        'body': json.dumps('PDF Listener function executed successfully')
    }