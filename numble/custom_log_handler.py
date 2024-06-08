import os
import logging
import requests
import json
import gzip

from io import BytesIO


class NewRelicLogHandler(logging.Handler):
    def __init__(self, api_key, log_api_url):
        super().__init__()
        self.api_key = api_key
        self.log_api_url = log_api_url

    def emit(self, record):

        log_entry = self.format(record)
        msg_logger = log_entry.split('&')
        log_entry = msg_logger[0] 
        try:
            logger = msg_logger[1]
        except IndexError:
            logger = ''
        log_data = [{
            "application": os.environ["NEW_RELIC_APP_NAME"],
            "debug_mode": bool(os.environ.get("DEBUG", default=0)),
            "level": record.levelname.lower(),
            "timestamp": record.created,
            "asctime": record.asctime,
            "created": record.created,
            "filename": record.filename,
            "funcName": record.funcName,
            "levelname": record.levelname,
            "module": record.module,
            "msg": log_entry,
            "name": record.name,
            "stack_info": record.stack_info,
            "logger": logger,
        }]

        log_data_json = json.dumps(log_data)

        buffer = BytesIO()
        with gzip.GzipFile(fileobj=buffer, mode='w') as f:
            f.write(log_data_json.encode('utf-8'))
        compressed_data = buffer.getvalue()

        headers = {
            'Content-Encoding': 'gzip',
            'Content-Type': 'application/json',
            'X-Insert-Key': self.api_key
        }

        response = requests.post(self.log_api_url, headers=headers, data=compressed_data)
        if response.status_code != 202:
            print(f'Failed to send logs: {response.status_code}')
            print(response.text)

# Configuration for New Relic
NEW_RELIC_API_KEY = os.environ['NEW_RELIC_API_KEY']
NEW_RELIC_LOG_API_URL = os.environ['NEW_RELIC_LOG_API_URL']
