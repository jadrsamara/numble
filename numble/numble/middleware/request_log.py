
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
        
        log_data = {
            "remote_address": request.META["REMOTE_ADDR"],
            "server_hostname": socket.gethostname(),
            "request_method": request.method,
            "request_body": request.POST.dict(),
            "request_url": request.build_absolute_uri(),
            "request_path": request.get_full_path(),
            "request": f"{request.method} '{request.get_full_path()}'",
            "request_cookies": request.COOKIES,
            "request_content_type": request.content_type,
            "session.id": request.COOKIES.get("sessionid", '-'),
        }

        # Only logging "*/api/*" patterns
        if "/api/" in str(request.get_full_path()):
            req_body = json.loads(request.body.decode("utf-8")) if request.body else {}
            log_data["request_body"] = req_body

        # request passes on to controller
        response = self.get_response(request)

        # add runtime to our log_data
        if response and response["content-type"] == "application/json":
            response_body = json.loads(response.content.decode("utf-8"))
            log_data["response_body"] = response_body
        log_data["run_time"] = time.monotonic() - start_time
        # log_data["run_time_readable"] = (log_data["run_time"])

        request_logger.info(msg=log_data["request"]+'&'+str({"logger":log_data}))

        return response

    # Log unhandled exceptions as well
    def process_exception(self, request, exception):
        try:
            raise exception
        except Exception as e:
            request_logger.exception("Unhandled Exception: " + str(e))
        return exception
