# Local AWS Setup

## Prerequisites

- Docker
- Docker Compose
- LocalStack `brew install localstack/tap/localstack-cli`
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
4. Run `python monitor_sqs.py watch`

## Usage

- Using postman to call the API Gateway endpoint provided in the output of `./scripts/setup_api_gateway.sh`
- Run `./scripts/upload_folder.sh` to upload multiple files to S3 you'll need to pass the path of the dir to this commmand `./scripts/upload_folder.sh ~/all_my_docs`

## Makefile

## When deploying for the first time
- `make deps` - Install dependencies for each Lambda function
- `make zip` - Zip each Lambda function
- `make deploy` - Deploy each Lambda function to LocalStack

## run make update after updating the code in a lambda function
- `make update` - Update each Lambda function code

## run make update-config after updating the configuration of a lambda function
- `make update-config` - Update each Lambda function configuration

## run make clean after updating the code in a lambda function
- `make clean` - Clean up

## Interact with the Container

### seed db records

`CONTAINER_ID=$(docker ps | grep final-function | awk '{print $1}')
docker exec -it $CONTAINER_ID /bin/bash -c "sqlite3 -column -header /tmp/lambda.db 'SELECT * FROM pdf_metadata;'"`

### list s3 bucket

`aws --endpoint-url=http://localhost:4566 s3 ls s3://pdf-uploads` 


### list API Gateway

`aws --endpoint-url=http://localhost:4566 apigateway get-rest-apis`

### list SQS queues

`aws --endpoint-url=http://localhost:4566 sqs list-queues`


