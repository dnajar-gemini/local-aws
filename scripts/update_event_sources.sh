#!/bin/bash

# Set variables
ENDPOINT="http://localhost:4566"
REGION="us-east-2"
QUEUE_A="queue-a"
QUEUE_B="queue-b"

echo "Getting existing event source mappings..."

# Get the UUID for the processor function event source mapping
PROCESSOR_UUID=$(aws --endpoint-url=$ENDPOINT --region $REGION lambda list-event-source-mappings \
  --function-name processor-function \
  --event-source-arn arn:aws:sqs:$REGION:000000000000:$QUEUE_A \
  --query 'EventSourceMappings[0].UUID' \
  --output text)

echo "Processor function event source mapping UUID: $PROCESSOR_UUID"

# Get the UUID for the final function event source mapping
FINAL_UUID=$(aws --endpoint-url=$ENDPOINT --region $REGION lambda list-event-source-mappings \
  --function-name final-function \
  --event-source-arn arn:aws:sqs:$REGION:000000000000:$QUEUE_B \
  --query 'EventSourceMappings[0].UUID' \
  --output text)

echo "Final function event source mapping UUID: $FINAL_UUID"

# Update the processor function event source mapping
if [ "$PROCESSOR_UUID" != "None" ]; then
  echo "Updating processor function event source mapping..."
  aws --endpoint-url=$ENDPOINT --region $REGION lambda update-event-source-mapping \
    --uuid $PROCESSOR_UUID \
    --batch-size 10 \
    --maximum-batching-window-in-seconds 5
else
  echo "No existing event source mapping found for processor function. Creating new one..."
  aws --endpoint-url=$ENDPOINT --region $REGION lambda create-event-source-mapping \
    --function-name processor-function \
    --event-source-arn arn:aws:sqs:$REGION:000000000000:$QUEUE_A \
    --batch-size 10 \
    --maximum-batching-window-in-seconds 5
fi

# Update the final function event source mapping
if [ "$FINAL_UUID" != "None" ]; then
  echo "Updating final function event source mapping..."
  aws --endpoint-url=$ENDPOINT --region $REGION lambda update-event-source-mapping \
    --uuid $FINAL_UUID \
    --batch-size 10 \
    --maximum-batching-window-in-seconds 5
else
  echo "No existing event source mapping found for final function. Creating new one..."
  aws --endpoint-url=$ENDPOINT --region $REGION lambda create-event-source-mapping \
    --function-name final-function \
    --event-source-arn arn:aws:sqs:$REGION:000000000000:$QUEUE_B \
    --batch-size 10 \
    --maximum-batching-window-in-seconds 5
fi

echo "Update complete!"
