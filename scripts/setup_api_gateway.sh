#!/bin/bash

# Set variables
ENDPOINT="http://localhost:4566"
REGION="us-east-2"
PRODUCER_FUNCTION_NAME="producer-function"

echo "Setting up API Gateway for producer function..."

# Get the producer function ARN
PRODUCER_ARN=$(aws --endpoint-url=$ENDPOINT --region $REGION lambda get-function \
  --function-name $PRODUCER_FUNCTION_NAME \
  --query 'Configuration.FunctionArn' \
  --output text)

# Create a REST API
API_ID=$(aws --endpoint-url=$ENDPOINT --region $REGION apigateway create-rest-api \
  --name "PDF-Upload-API" \
  --query 'id' \
  --output text)

echo "Created API Gateway with ID: $API_ID"

# Get the root resource ID
ROOT_RESOURCE_ID=$(aws --endpoint-url=$ENDPOINT --region $REGION apigateway get-resources \
  --rest-api-id $API_ID \
  --query 'items[0].id' \
  --output text)

# Create a resource for file
FILE_RESOURCE_ID=$(aws --endpoint-url=$ENDPOINT --region $REGION apigateway create-resource \
  --rest-api-id $API_ID \
  --parent-id $ROOT_RESOURCE_ID \
  --path-part "file" \
  --query 'id' \
  --output text)

echo "Created resource /file with ID: $FILE_RESOURCE_ID"

# Create a resource for file uploads
RESOURCE_ID=$(aws --endpoint-url=$ENDPOINT --region $REGION apigateway create-resource \
  --rest-api-id $API_ID \
  --parent-id $FILE_RESOURCE_ID \
  --path-part "upload" \
  --query 'id' \
  --output text)

echo "Created resource /file/upload with ID: $RESOURCE_ID"

# Create a POST method
aws --endpoint-url=$ENDPOINT --region $REGION apigateway put-method \
  --rest-api-id $API_ID \
  --resource-id $RESOURCE_ID \
  --http-method POST \
  --authorization-type NONE

echo "Created POST method for /file/upload"

# Set up Lambda integration
aws --endpoint-url=$ENDPOINT --region $REGION apigateway put-integration \
  --rest-api-id $API_ID \
  --resource-id $RESOURCE_ID \
  --http-method POST \
  --type AWS_PROXY \
  --integration-http-method POST \
  --uri "arn:aws:apigateway:$REGION:lambda:path/2015-03-31/functions/$PRODUCER_ARN/invocations"

echo "Set up Lambda integration with producer function"

# Add permission for API Gateway to invoke Lambda
aws --endpoint-url=$ENDPOINT --region $REGION lambda add-permission \
  --function-name $PRODUCER_FUNCTION_NAME \
  --statement-id apigateway-test \
  --action lambda:InvokeFunction \
  --principal apigateway.amazonaws.com \
  --source-arn "arn:aws:execute-api:$REGION:000000000000:$API_ID/*/POST/file/upload"

echo "Added permission for API Gateway to invoke Lambda"

# Deploy the API
DEPLOYMENT_ID=$(aws --endpoint-url=$ENDPOINT --region $REGION apigateway create-deployment \
  --rest-api-id $API_ID \
  --stage-name prod \
  --query 'id' \
  --output text)

echo "Deployed API to stage 'prod' with deployment ID: $DEPLOYMENT_ID"

# Get the API endpoint URL
API_ENDPOINT="http://localhost:4566/restapis/$API_ID/prod/_user_request_/file/upload"

echo "API Gateway setup complete!"
echo "API Endpoint URL: $API_ENDPOINT"
echo ""
