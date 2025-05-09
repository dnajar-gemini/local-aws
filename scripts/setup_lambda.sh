#!/bin/bash

# Set variables
ENDPOINT="http://localhost:4566"
REGION="us-east-2"
ROLE_ARN="arn:aws:iam::000000000000:role/lambda-role"
BUCKET_NAME="pdf-uploads"
QUEUE_A="queue-a"
QUEUE_B="queue-b"

# Create S3 bucket
echo "Creating S3 bucket: $BUCKET_NAME"
aws --endpoint-url=$ENDPOINT --region $REGION s3 mb s3://$BUCKET_NAME

# Create SQS queues
echo "Creating SQS queues: $QUEUE_A and $QUEUE_B"
QUEUE_A_URL=$(aws --endpoint-url=$ENDPOINT --region $REGION sqs create-queue --queue-name $QUEUE_A --query 'QueueUrl' --output text)
QUEUE_B_URL=$(aws --endpoint-url=$ENDPOINT --region $REGION sqs create-queue --queue-name $QUEUE_B --query 'QueueUrl' --output text)

echo "Queue A URL: $QUEUE_A_URL"
echo "Queue B URL: $QUEUE_B_URL"

# Create Lambda functions
echo "Creating Lambda functions..."

# Create pdf_listener function
aws --endpoint-url=$ENDPOINT --region $REGION lambda create-function \
  --function-name pdf_listener-function \
  --runtime python3.9 \
  --handler app.lambda_handler \
  --zip-file fileb://lambda/pdf_listener/function.zip \
  --role $ROLE_ARN \
  --timeout 30 \
  --environment "Variables={AWS_ENDPOINT_URL=$ENDPOINT,AWS_REGION=$REGION,S3_BUCKET_NAME=$BUCKET_NAME,SQS_QUEUE_A=$QUEUE_A}"

# Create processor function
aws --endpoint-url=$ENDPOINT --region $REGION lambda create-function \
  --function-name processor-function \
  --runtime python3.9 \
  --handler app.lambda_handler \
  --zip-file fileb://lambda/processor/function.zip \
  --role $ROLE_ARN \
  --timeout 30 \
  --environment "Variables={AWS_ENDPOINT_URL=$ENDPOINT,AWS_REGION=$REGION,SQS_QUEUE_A=$QUEUE_A,SQS_QUEUE_B=$QUEUE_B}"

# Create final function
aws --endpoint-url=$ENDPOINT --region $REGION lambda create-function \
  --function-name final-function \
  --runtime python3.9 \
  --handler app.lambda_handler \
  --zip-file fileb://lambda/final/function.zip \
  --role $ROLE_ARN \
  --timeout 30 \
  --environment "Variables={AWS_ENDPOINT_URL=$ENDPOINT,AWS_REGION=$REGION,SQS_QUEUE_B=$QUEUE_B}"

# Create producer function
aws --endpoint-url=$ENDPOINT --region $REGION lambda create-function \
  --function-name producer-function \
  --runtime python3.9 \
  --handler app.lambda_handler \
  --zip-file fileb://lambda/producer/function.zip \
  --role $ROLE_ARN \
  --timeout 30 \
  --environment "Variables={AWS_ENDPOINT_URL=$ENDPOINT,AWS_REGION=$REGION,S3_BUCKET_NAME=$BUCKET_NAME}"

# Set up S3 event trigger for pdf_listener
echo "Setting up S3 event trigger for pdf_listener..."
# First, get the function ARN
FUNCTION_ARN=$(aws --endpoint-url=$ENDPOINT --region $REGION lambda get-function --function-name pdf_listener-function --query 'Configuration.FunctionArn' --output text)

# Add permission for S3 to invoke the Lambda function
aws --endpoint-url=$ENDPOINT --region $REGION lambda add-permission \
  --function-name pdf_listener-function \
  --statement-id s3-trigger \
  --action lambda:InvokeFunction \
  --principal s3.amazonaws.com \
  --source-arn arn:aws:s3:::$BUCKET_NAME

# Create a temporary JSON file for the notification configuration
cat > /tmp/notification.json << EOF
{
  "LambdaFunctionConfigurations": [
    {
      "LambdaFunctionArn": "$FUNCTION_ARN",
      "Events": ["s3:ObjectCreated:*"]
    }
  ]
}
EOF

# Apply the notification configuration
aws --endpoint-url=$ENDPOINT --region $REGION s3api put-bucket-notification-configuration \
  --bucket $BUCKET_NAME \
  --notification-configuration file:///tmp/notification.json

# Set up SQS triggers for processor and final functions with increased batch size
echo "Setting up SQS trigger for processor function..."
aws --endpoint-url=$ENDPOINT --region $REGION lambda create-event-source-mapping \
  --function-name processor-function \
  --event-source-arn arn:aws:sqs:$REGION:000000000000:$QUEUE_A \
  --batch-size 10 \
  --maximum-batching-window-in-seconds 5

echo "Setting up SQS trigger for final function..."
aws --endpoint-url=$ENDPOINT --region $REGION lambda create-event-source-mapping \
  --function-name final-function \
  --event-source-arn arn:aws:sqs:$REGION:000000000000:$QUEUE_B \
  --batch-size 10 \
  --maximum-batching-window-in-seconds 5

echo "Setup complete!"
