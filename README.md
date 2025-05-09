# Local AWS Setup

## Prerequisites

- Docker
- Docker Compose
- LocalStack
- AWS CLI
- Python 3.8

## AWS Services

- SQS
- S3
- Lambda
- API Gateway

## Setup

1. Run `docker compose up -d`
2. Run `./scripts/setup_lambda.sh`
3. Run `./scripts/setup_api_gateway.sh`
4. Run `./monitor_sqs.py`

## Usage

- Using postman to call the API Gateway endpoint provided in the output of `./scripts/setup_api_gateway.sh`
- Run `./scripts/upload_folder.sh` to upload multiple files to S3

## Makefile

- `make deps` - Install dependencies for each Lambda function
- `make zip` - Zip each Lambda function
- `make deploy` - Deploy each Lambda function to LocalStack
- `make update` - Update each Lambda function code
- `make update-config` - Update each Lambda function configuration
- `make clean` - Clean up



