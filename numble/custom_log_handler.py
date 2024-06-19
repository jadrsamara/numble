import os
import logging
import requests
import json
import gzip

from io import BytesIO

# Configuration for New Relic
NEW_RELIC_API_KEY = os.environ['NEW_RELIC_API_KEY']
NEW_RELIC_LOG_API_URL = os.environ['NEW_RELIC_LOG_API_URL']


class NewRelicLogHandler(logging.Handler):
    def __init__(self, api_key, log_api_url):
        super().__init__()
        self.api_key = api_key
        self.log_api_url = log_api_url

    def emit(self, record):

        parsed_request = getattr(record, 'parsed_request', {})
        request = getattr(record, 'request', {})
        logger_data = getattr(record, 'log_data', {})
        is_request_log = getattr(record, 'request_log', {})

        log_entry = self.format(record)

        is_wsgi_request = False
        if str(type(request)).__contains__('wsgi'):
            is_wsgi_request = True

        logger_request = None

        if is_request_log != True and request != {} and is_wsgi_request:
            parsed_request = {
                "request_method": request.method,
                "request_body": request.POST.dict(),
                "request_url": request.build_absolute_uri(),
                "request_path": request.get_full_path(),
                "request": f"'{request.method} {request.get_full_path()}'",
                "request_cookies": request.COOKIES,
                "request_content_type": request.content_type,
                "request.user": str(request.user),
            }
            logger_request = f"'{request.method} {request.get_full_path()}'"

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
            "logger.request": logger_request,
            "logger": json.dumps(logger_data),
            "request": parsed_request,
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

        try:
            response = requests.post(self.log_api_url, headers=headers, data=compressed_data)
            if response.status_code != 202:
                print(f'Failed to send logs: {response.status_code}')
                print(response.text)
        except requests.exceptions.ConnectionError as e:
            print(e)

