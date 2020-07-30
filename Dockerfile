FROM python:3.7.4

RUN mkdir -p /home/cisconverter
WORKDIR /home/cisconverter

RUN pip install --upgrade pip

ADD requirements.txt .
RUN pip install -r requirements.txt
RUN pip install gunicorn

ADD boot.sh ./
RUN chmod +x boot.sh

ENV FLASK_APP converter.py

EXPOSE 8300
ENTRYPOINT ["./boot.sh"]