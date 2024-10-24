#!/usr/bin/env python
import os
import sys

from django.core.management import execute_from_command_line
from django.core.wsgi import get_wsgi_application

# Set the default settings module for the 'manage.py' command.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'your_project_name.settings')  # Replace 'your_project_name' with your actual project name.

# Create the WSGI application callable.
application = get_wsgi_application()

if __name__ == '__main__':
    execute_from_command_line(sys.argv)
