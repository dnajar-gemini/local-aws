import json
import sqlite3
import os
import datetime
import traceback
import sys

# Add the parent directory to sys.path to import the config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    from config import ENDPOINT_URL, REGION, SQLITE_DB_PATH
    print(f"Config loaded successfully: ENDPOINT_URL={ENDPOINT_URL}, REGION={REGION}, SQLITE_DB_PATH={SQLITE_DB_PATH}")
except Exception as e:
    print(f"Error loading config: {str(e)}")
    # Fallback to hardcoded values
    ENDPOINT_URL = "http://localstack:4566"
    REGION = "us-east-2"
    SQLITE_DB_PATH = '/tmp/lambda.db'
    print(f"Using fallback config: ENDPOINT_URL={ENDPOINT_URL}, REGION={REGION}, SQLITE_DB_PATH={SQLITE_DB_PATH}")

def lambda_handler(event, context):
    print("========== FINAL FUNCTION INVOKED ==========")
    print(f"Event: {json.dumps(event)}")
    print("===========================================")
    
    db_path = SQLITE_DB_PATH

    try:
        # Setup DB
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute('''
            CREATE TABLE IF NOT EXISTS pdf_metadata (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT,
                bucket TEXT,
                status TEXT,
                tag TEXT,
                size INTEGER,
                signature TEXT,
                source TEXT,
                timestamp TEXT,
                processed_timestamp TEXT,
                inserted_at TEXT
            )
        ''')
        
        records_processed = 0
        
        for record in event['Records']:
            try:
                body = json.loads(record['body'])
                print(f"Processing record: {json.dumps(body)}")

                # Current timestamp for when the record is inserted
                current_time = datetime.datetime.now().isoformat()
                
                # Extract the timestamp from the message or use current time
                timestamp = body.get('timestamp', current_time)
                processed_timestamp = body.get('processed_timestamp', '')
                
                # If processed_timestamp is a number (Unix timestamp), convert to ISO format
                if isinstance(processed_timestamp, (int, float)) or (isinstance(processed_timestamp, str) and processed_timestamp.isdigit()):
                    try:
                        processed_timestamp = datetime.datetime.fromtimestamp(float(processed_timestamp)).isoformat()
                    except:
                        # If conversion fails, keep original
                        pass

                cur.execute('''
                    INSERT INTO pdf_metadata (
                        filename, bucket, status, tag, 
                        size, signature, source, timestamp, 
                        processed_timestamp, inserted_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    body.get('filename', os.path.basename(body.get('key', ''))),
                    body.get('bucket', ''),
                    body.get('status', 'unknown'),
                    body.get('tag', 'untagged'),
                    body.get('size', 0),
                    body.get('signature', ''),
                    body.get('source', ''),
                    timestamp,
                    processed_timestamp,
                    current_time
                ))
                
                records_processed += 1
                print(f"✅ Inserted complete metadata for {body.get('filename', body.get('key', 'unknown file'))}")
            
            except Exception as e:
                print(f"Error processing record: {str(e)}")
                traceback.print_exc()
                continue

        # Commit changes and close connection
        conn.commit()
        
        # Print some stats about the database
        cur.execute("SELECT COUNT(*) FROM pdf_metadata")
        total_records = cur.fetchone()[0]
        print(f"Total records in database: {total_records}")
        
        conn.close()

        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Metadata persisted.',
                'records_processed': records_processed,
                'total_records': total_records
            })
        }
    except Exception as e:
        print(f"Error in final function: {str(e)}")
        traceback.print_exc()
        return {
            'statusCode': 500,
            'body': json.dumps({
                'message': f'Error: {str(e)}'
            })
        }
