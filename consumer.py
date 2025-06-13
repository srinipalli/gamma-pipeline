from kafka import KafkaConsumer
import json
import re
from pymongo import MongoClient
from datetime import datetime

# Kafka and MongoDB settings
KAFKA_BROKER = 'localhost:9092'
TOPIC = 'test'
MONGO_URI = 'mongodb+srv://mvishaalgokul8:IMTXb7QXknOIgFaw@infrahealth.vdxwhfq.mongodb.net/'
DB_NAME = 'logs'
APP_COLLECTION = 'app'
CPU_COLLECTION = 'server'

# Regex for parsing Spring Boot app log
app_log_regex = re.compile(
    r'^(?P<timestamp>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3})\s+'
    r'(?P<level>INFO|ERROR|WARN|DEBUG|TRACE)\s+'
    r'(?P<pid>\d+)\s+---\s+\[(?P<thread>[^\]]+)\]\s+'
    r'(?P<logger>[\w\.]+)\s*:\s*(?P<msg>[\s\S]*)'
)

# Connect to MongoDB
mongo_client = MongoClient(MONGO_URI)
db = mongo_client[DB_NAME]
app_col = db[APP_COLLECTION]
cpu_col = db[CPU_COLLECTION]

# Kafka consumer
consumer = KafkaConsumer(
    TOPIC,
    bootstrap_servers=[KAFKA_BROKER],
    auto_offset_reset='earliest',
    enable_auto_commit=True,
    group_id='log-parser-consumer'
)

print("Starting Kafka consumer...")

for message in consumer:
    try:
        decoded = message.value.decode('utf-8')
        if not decoded.strip():
            continue
        
        data = json.loads(decoded)
        log_type = data.get('log_type')

        if log_type == 'app_log':
            msg = data['message'].replace('\r\n', '\n')
            match = app_log_regex.match(msg)
            
            if match:
                # Extract parsed fields from regex
                app_data = match.groupdict()
                lines = app_data['msg'].split('\n')
                app_data['message'] = lines[0]
                
                # Parse exception and stacktrace
                if len(lines) > 1 and lines[1].startswith('java.'):
                    exc_line = lines[1]
                    m = re.match(r'java\.([A-Za-z0-9_]+Exception): (.*)', exc_line)
                    if m:
                        app_data['exception_type'] = m.group(1)
                        app_data['exception_message'] = m.group(2)
                    stacktrace = [line.strip() for line in lines[2:] if line.strip().startswith('at ')]
                    if stacktrace:
                        app_data['stacktrace'] = stacktrace
                
                # Remove the original 'msg' field
                del app_data['msg']
                
                # PRESERVE FLUENTD METADATA
                app_data['environment'] = data.get('environment')
                app_data['server'] = data.get('server') 
                app_data['app_name'] = data.get('app_name')
                app_data['path'] = data.get('path')
                app_data['log_type'] = data.get('log_type')
                
                # Add createdAt timestamp
                app_data['createdAt'] = datetime.utcnow()
                
                print(f"Sending structured app_log to MongoDB: Environment={app_data.get('environment')}, Server={app_data.get('server')}, App={app_data.get('app_name')}, Level={app_data.get('level')}")
                app_col.insert_one(app_data)
                
            else:
                # Save raw if regex fails, preserving ALL original data
                raw_data = {
                    'raw': data['message'],
                    'environment': data.get('environment'),
                    'server': data.get('server'),
                    'app_name': data.get('app_name'),
                    'path': data.get('path'),
                    'log_type': data.get('log_type'),
                    'createdAt': datetime.utcnow()
                }
                print(f"Sending raw app_log to MongoDB: Environment={raw_data.get('environment')}, Server={raw_data.get('server')}, App={raw_data.get('app_name')}")
                app_col.insert_one(raw_data)

        elif log_type == 'cpu_log':
            # CPU logs already have metadata from Fluentd, just add timestamp
            data['createdAt'] = datetime.utcnow()
            print(f"Sending cpu_log to MongoDB: Environment={data.get('environment')}, Server={data.get('server')}, Health={data.get('server_health')}")
            cpu_col.insert_one(data)
        
        else:
            print(f"Unknown log_type: {log_type}")

    except json.JSONDecodeError as e:
        print(f"JSON decode error: {e}")
        continue
    except Exception as e:
        print(f"Error processing message: {str(e)}")
        continue

print("Kafka consumer stopped.")
