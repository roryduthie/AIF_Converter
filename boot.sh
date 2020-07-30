#!/bin/sh
source venv/bin/activate
exec gunicorn --chdir /home/cisconverter/ -b :8300 --access-logfile - --error-logfile - converter:app --timeout 3000
