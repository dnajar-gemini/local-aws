import boto3
import json
import time
import sys
from datetime import datetime

# Configure the AWS client
endpoint_url = 'http://localhost:4566'
region = 'us-east-2'

# Create SQS client
sqs = boto3.client('sqs', endpoint_url=endpoint_url, region_name=region)

def get_queue_stats(queue_name):
    """Get statistics for a specific queue"""
    try:
        # Get queue URL
        queue_url_response = sqs.get_queue_url(QueueName=queue_name)
        queue_url = queue_url_response['QueueUrl']
        
        # Get queue attributes
        attributes = sqs.get_queue_attributes(
            QueueUrl=queue_url,
            AttributeNames=['All']
        )
        
        # Extract relevant stats
        stats = {
            'QueueName': queue_name,
            'QueueURL': queue_url,
            'ApproximateNumberOfMessages': int(attributes['Attributes'].get('ApproximateNumberOfMessages', 0)),
            'ApproximateNumberOfMessagesNotVisible': int(attributes['Attributes'].get('ApproximateNumberOfMessagesNotVisible', 0)),
            'ApproximateNumberOfMessagesDelayed': int(attributes['Attributes'].get('ApproximateNumberOfMessagesDelayed', 0)),
            'CreatedTimestamp': attributes['Attributes'].get('CreatedTimestamp', 'N/A'),
            'LastModifiedTimestamp': attributes['Attributes'].get('LastModifiedTimestamp', 'N/A')
        }
        
        return stats
    except Exception as e:
        print(f"Error getting stats for queue {queue_name}: {str(e)}")
        return None

def list_all_queues():
    """List all queues and their stats"""
    try:
        response = sqs.list_queues()
        
        if 'QueueUrls' not in response:
            print("No queues found")
            return []
        
        queue_urls = response['QueueUrls']
        queues = []
        
        for url in queue_urls:
            # Extract queue name from URL
            queue_name = url.split('/')[-1]
            queues.append(queue_name)
        
        return queues
    except Exception as e:
        print(f"Error listing queues: {str(e)}")
        return []

def monitor_queues(queue_names=None, interval=5, count=None):
    """Monitor queues continuously or for a specific number of times"""
    if queue_names is None:
        queue_names = list_all_queues()
        
    if not queue_names:
        print("No queues to monitor")
        return
    
    iteration = 0
    try:
        while count is None or iteration < count:
            # Clear screen in terminal
            print("\033c", end="")
            
            print(f"\n===== SQS Queue Monitor - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} =====")
            
            for queue_name in queue_names:
                stats = get_queue_stats(queue_name)
                if stats:
                    print(f"\nQueue: {stats['QueueName']}")
                    print(f"URL: {stats['QueueURL']}")
                    print(f"Messages Available: {stats['ApproximateNumberOfMessages']}")
                    print(f"Messages In Flight: {stats['ApproximateNumberOfMessagesNotVisible']}")
                    print(f"Messages Delayed: {stats['ApproximateNumberOfMessagesDelayed']}")
                    
                    # Show all messages in the queue
                    if stats['ApproximateNumberOfMessages'] > 0:
                        print("\nMessages in queue:")
                        peek_messages(queue_name, count=stats['ApproximateNumberOfMessages'])
            
            if count is not None:
                iteration += 1
                if iteration >= count:
                    break
                    
            if count is None or iteration < count:
                print(f"\nRefreshing in {interval} seconds... (Ctrl+C to exit)")
                time.sleep(interval)
    except KeyboardInterrupt:
        print("\nMonitoring stopped by user")

def peek_messages(queue_name, count=10):
    """Peek at messages in a queue without removing them"""
    try:
        # Get queue URL
        queue_url_response = sqs.get_queue_url(QueueName=queue_name)
        queue_url = queue_url_response['QueueUrl']
        
        # Receive messages with a very short visibility timeout
        response = sqs.receive_message(
            QueueUrl=queue_url,
            MaxNumberOfMessages=min(10, count),  # SQS limits to 10 messages per request
            VisibilityTimeout=1,  # Set to 1 second so messages become visible again quickly
            WaitTimeSeconds=1
        )
        
        if 'Messages' in response:
            messages = response['Messages']
            
            # If we need more messages and there are likely more available
            if count > 10 and len(messages) == 10:
                # Make additional requests to get more messages
                for _ in range((count - 10) // 10 + 1):
                    # Wait a moment for visibility timeout to expire
                    time.sleep(1.1)
                    
                    additional_response = sqs.receive_message(
                        QueueUrl=queue_url,
                        MaxNumberOfMessages=10,
                        VisibilityTimeout=1,
                        WaitTimeSeconds=1
                    )
                    
                    if 'Messages' in additional_response:
                        messages.extend(additional_response['Messages'])
                        if len(messages) >= count:
                            break
            
            print(f"\nFound {len(messages)} messages in {queue_name}:")
            for i, msg in enumerate(messages):
                print(f"\n--- Message {i+1} ---")
                print(f"ID: {msg['MessageId']}")
                
                # Try to parse as JSON for better display
                try:
                    body = json.loads(msg['Body'])
                    print(f"Body: {json.dumps(body, indent=2)}")
                except:
                    # If not JSON, print as is
                    print(f"Body: {msg['Body']}")
                
                if 'Attributes' in msg:
                    print("Attributes:")
                    for key, value in msg['Attributes'].items():
                        print(f"  {key}: {value}")
        else:
            print(f"\nNo messages found in {queue_name}")
            
    except Exception as e:
        print(f"Error peeking at messages in queue {queue_name}: {str(e)}")

def watch_queues(interval=2):
    """Watch queues in real-time with continuous updates"""
    try:
        while True:
            # Clear screen
            print("\033c", end="")
            
            # Get all queues
            queues = list_all_queues()
            
            if not queues:
                print("No queues found. Make sure LocalStack is running and SQS is enabled.")
                time.sleep(interval)
                continue
                
            print(f"===== SQS Queue Monitor (WATCH MODE) - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} =====")
            print(f"Found {len(queues)} queues: {', '.join(queues)}")
            print("Press Ctrl+C to exit watch mode\n")
            
            # Show stats for each queue
            for queue_name in queues:
                stats = get_queue_stats(queue_name)
                if stats:
                    print(f"Queue: {stats['QueueName']}")
                    print(f"  Messages Available: {stats['ApproximateNumberOfMessages']}")
                    print(f"  Messages In Flight: {stats['ApproximateNumberOfMessagesNotVisible']}")
                    
                    # If there are messages, show all of them
                    if stats['ApproximateNumberOfMessages'] > 0:
                        try:
                            queue_url = stats['QueueURL']
                            response = sqs.receive_message(
                                QueueUrl=queue_url,
                                MaxNumberOfMessages=10,
                                VisibilityTimeout=1,
                                WaitTimeSeconds=1
                            )
                            
                            if 'Messages' in response:
                                print(f"  Messages in queue:")
                                for i, msg in enumerate(response['Messages']):
                                    try:
                                        body = json.loads(msg['Body'])
                                        print(f"    {i+1}: {json.dumps(body)}")
                                    except:
                                        print(f"    {i+1}: {msg['Body']}")
                                
                                # If there are more messages than we received
                                if stats['ApproximateNumberOfMessages'] > len(response['Messages']):
                                    print(f"    ... and approximately {stats['ApproximateNumberOfMessages'] - len(response['Messages'])} more")
                        except Exception as e:
                            print(f"  Error peeking at messages: {str(e)}")
                    
                    print("")
            
            time.sleep(interval)
    except KeyboardInterrupt:
        print("\nWatch mode stopped by user")

def dump_all_messages(queue_name):
    """Dump all messages from a queue to the console without removing them"""
    try:
        stats = get_queue_stats(queue_name)
        if not stats:
            print(f"Could not get stats for queue {queue_name}")
            return
            
        message_count = stats['ApproximateNumberOfMessages']
        if message_count == 0:
            print(f"No messages in queue {queue_name}")
            return
            
        print(f"Dumping all {message_count} messages from {queue_name}...")
        peek_messages(queue_name, count=message_count)
        
    except Exception as e:
        print(f"Error dumping messages from queue {queue_name}: {str(e)}")

if __name__ == "__main__":
    print("SQS Queue Monitor for LocalStack")
    print("================================")
    
    # Check if watch mode is requested
    if len(sys.argv) > 1:
        if sys.argv[1].lower() == "watch":
            interval = 2
            if len(sys.argv) > 2:
                try:
                    interval = int(sys.argv[2])
                except:
                    pass
            watch_queues(interval)
        elif sys.argv[1].lower() == "dump" and len(sys.argv) > 2:
            # Dump all messages from a specific queue
            dump_all_messages(sys.argv[2])
        else:
            # Assume it's a queue name and dump all messages
            dump_all_messages(sys.argv[1])
    else:
        # List all queues
        queues = list_all_queues()
        
        if not queues:
            print("No queues found. Make sure LocalStack is running and SQS is enabled.")
        else:
            print(f"Found {len(queues)} queues: {', '.join(queues)}")
            
            # Monitor all queues once
            monitor_queues(queues, count=1)
            
            # Peek at messages in each queue
            for queue in queues:
                peek_messages(queue)
                
            print("\nTo continuously monitor queues, run:")
            print("python monitor_sqs.py watch [interval_seconds]")
            print("\nTo dump all messages from a specific queue, run:")
            print("python monitor_sqs.py dump <queue_name>")
            print("  or simply:")
            print("python monitor_sqs.py <queue_name>")
