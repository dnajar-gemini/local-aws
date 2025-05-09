import json
import boto3
import traceback
import time
import datetime
import sys
import os

# Add the parent directory to sys.path to import the config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    from config import ENDPOINT_URL, REGION, SQS_QUEUE_B
    print(f"Config loaded successfully: ENDPOINT_URL={ENDPOINT_URL}, REGION={REGION}, SQS_QUEUE_B={SQS_QUEUE_B}")
except Exception as e:
    print(f"Error loading config: {str(e)}")
    # Fallback to hardcoded values
    ENDPOINT_URL = "http://localstack:4566"
    REGION = "us-east-2"
    SQS_QUEUE_B = "queue-b"
    print(f"Using fallback config: ENDPOINT_URL={ENDPOINT_URL}, REGION={REGION}, SQS_QUEUE_B={SQS_QUEUE_B}")

# Use localstack endpoint for SQS
try:
    sqs = boto3.client("sqs", endpoint_url=ENDPOINT_URL, region_name=REGION)
    print("SQS client initialized successfully")
except Exception as e:
    print(f"Error initializing SQS client: {str(e)}")
    traceback.print_exc()

def lambda_handler(event, context):
    print("========== PROCESSOR FUNCTION INVOKED ==========")
    print(f"Event: {json.dumps(event)}")
    print("==============================================")
    
    records = []
    for record in event['Records']:
        try:
            body = json.loads(record['body'])
            print(f"Processing record: {json.dumps(body)}")

            # Validate
            key = body.get('key', '')
            if not key.lower().endswith('.pdf'):
                print(f" Skipping non-PDF file: {key}")
                continue

            # Generate proper timestamps
            current_timestamp = int(time.time())
            iso_timestamp = datetime.datetime.now().isoformat()

            structure_data = {
                'bucket': body['bucket'],
                'key': key,
                'status': 'validated',
                'source': 'processor',
                'filename': key.split('/')[-1],
                'tag': 'uploaded_pdf',
                'size': body.get('size', 0),
                'signature': body.get('signature', ''),
                'timestamp': iso_timestamp,
                'processed_timestamp': str(context.invoked_function_arn),
                'processor_id': context.function_name if context else 'processor-function'
            }

            # Send to queue-b
            try:
                # Get queue URL
                queue_url = f"{ENDPOINT_URL}/000000000000/{SQS_QUEUE_B}"
                
                # Send message
                response = sqs.send_message(
                    QueueUrl=queue_url,
                    MessageBody=json.dumps(structure_data)
                )
                print(f" Message sent to queue-b: {response['MessageId']}")
                records.append(structure_data)
            except Exception as sqs_error:
                print(f"Error sending message to SQS queue-b: {str(sqs_error)}")
                traceback.print_exc()
                
        except Exception as e:
            print(f"Error processing record: {str(e)}")
            traceback.print_exc()
            continue

    return {
        'statusCode': 200,
        'body': json.dumps({
            'processed': len(records)
        })
    }
