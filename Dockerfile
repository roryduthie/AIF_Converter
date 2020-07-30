FROM python:3.7.4

ADD converter.py /home/cisconverter/
WORKDIR /home/cisconverter

RUN pip install --upgrade pip

ADD requirements.txt .
RUN pip install -r requirements.txt
RUN pip install gunicorn

ADD boot.sh ./
RUN chmod +x boot.sh

ENV FLASK_APP converter.py

EXPOSE 8300
CMD gunicorn -b :8300 --access-logfile - --error-logfile - converter:app --timeout 3000