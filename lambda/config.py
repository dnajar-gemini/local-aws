import os

# AWS Service endpoints - use localstack for internal container communication
ENDPOINT_URL = os.environ.get('AWS_ENDPOINT_URL', 'http://localstack:4566')
REGION = os.environ.get('AWS_REGION', 'us-east-2')

# S3 configuration
S3_BUCKET_NAME = os.environ.get('S3_BUCKET_NAME', 'pdf-uploads')

# SQS configuration
SQS_QUEUE_A = os.environ.get('SQS_QUEUE_A', 'queue-a')
SQS_QUEUE_B = os.environ.get('SQS_QUEUE_B', 'queue-b')

# SQLite configuration (for final function)
SQLITE_DB_PATH = os.environ.get('SQLITE_DB_PATH', '/tmp/lambda.db')
