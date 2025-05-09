#!/bin/bash

# Set variables
ENDPOINT="http://localhost:4566"
REGION="us-east-2"
BUCKET_NAME="pdf-uploads"

# Check if a folder path was provided
if [ -z "$1" ]; then
  echo "Please provide a folder path to upload."
  echo "Usage: $0 /test_pdf"
  exit 1
fi

FOLDER_PATH="$1"

# Check if the folder exists
if [ ! -d "$FOLDER_PATH" ]; then
  echo "Folder does not exist: $FOLDER_PATH"
  exit 1
fi

echo "Uploading files from $FOLDER_PATH to S3 bucket $BUCKET_NAME..."

# Count total files
TOTAL_FILES=$(find "$FOLDER_PATH" -type f | wc -l)
echo "Found $TOTAL_FILES files to upload."

# Upload each file
COUNT=0
SUCCESSFUL=0
FAILED=0

for file in $(find "$FOLDER_PATH" -type f); do
  filename=$(basename "$file")
  COUNT=$((COUNT + 1))
  
  echo "[$COUNT/$TOTAL_FILES] Uploading $filename..."
  
  # Upload the file to S3
  aws --endpoint-url=$ENDPOINT --region $REGION s3 cp "$file" "s3://$BUCKET_NAME/$filename"
  
  if [ $? -eq 0 ]; then
    echo "✅ Successfully uploaded $filename"
    SUCCESSFUL=$((SUCCESSFUL + 1))
  else
    echo "❌ Failed to upload $filename"
    FAILED=$((FAILED + 1))
  fi
done

echo "Upload complete!"
echo "Summary:"
echo "- Total files: $TOTAL_FILES"
echo "- Successfully uploaded: $SUCCESSFUL"
echo "- Failed: $FAILED"

# Check if any files were uploaded successfully
if [ $SUCCESSFUL -gt 0 ]; then
  echo "Files are available at: http://localhost:4566/$BUCKET_NAME/"
fi
