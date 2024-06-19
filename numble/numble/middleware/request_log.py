
"""
Middleware to log `*/api/*` requests and responses.
"""
import socket
import time
import json
import logging

request_logger = logging.getLogger("django")

class RequestLogMiddleware:
    """Request Logging Middleware."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start_time = time.monotonic()

        # request passes on to controller
        response = self.get_response(request)

        try:
            response.status_code
        except AttributeError:
            response.status_code = 500
            response.reason_phrase = 'Internal Server Error'

        parsed_request = {
            "request_method": request.method,
            "request_body": request.POST.dict(),
            "request_url": request.build_absolute_uri(),
            "request_path": request.get_full_path(),
            "request_cookies": request.COOKIES,
            "request_content_type": request.content_type,
            "request.user": str(request.user),
        }

        log_data = {
            "remote_address": request.META.get("REMOTE_ADDR", ''),
            "server_hostname": socket.gethostname(),
            "response.status_code": response.status_code,
            "response.reason_phrase": response.reason_phrase,
            "session.id": request.COOKIES.get("sessionid", '-'),
            "url_scheme": request.META.get("wsgi.url_scheme", ''),
            "request": f"'{request.method} {request.get_full_path()}' {response.status_code} {response.reason_phrase}",
        }

        for http_header in request.META.keys():
            if http_header.lower().startswith('http'):
                parsed_request[http_header] = request.META.get(http_header)

        parsed_request['client.ip'] = request.META.get('HTTP_X_FORWARDED_FOR', '-, -').split(', ')[0]
        log_data['logger.client.ip'] = request.META.get('HTTP_X_FORWARDED_FOR', '-, -').split(', ')[0]

        # Only logging "*/api/*" patterns
        if "/api/" in str(request.get_full_path()):
            req_body = json.loads(request.body.decode("utf-8")) if request.body else {}
            parsed_request["request_body"] = req_body

        # add runtime to our log_data
        try:
            if response and response["content-type"] == "application/json":
                response_body = json.loads(response.content.decode("utf-8"))
                log_data["response_body"] = response_body
            log_data["run_time"] = f'{time.monotonic() - start_time:.2f}s'
        except TypeError:
            log_data["run_time"] = 'no response'

        # request_logger.info(msg=log_data["request"]+'&'+json.dumps(log_data))
        request_logger.info(msg=log_data["request"], extra={'parsed_request': parsed_request, 'log_data': log_data, 'request_log': True})

        return response

    # # Log unhandled exceptions as well
    # def process_exception(self, request, exception):
    #     try:
    #         raise exception
    #     except Exception as e:
    #         request_logger.exception("Unhandled Exception: " + str(e))
    #     return exception
