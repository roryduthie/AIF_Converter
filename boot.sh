#!/bin/sh
source venv/bin/activate
exec gunicorn -b :8300 --access-logfile - --error-logfile - cisconverter --timeout 3000
