FROM tiangolo/uwsgi-nginx-flask:python3.8-alpine

WORKDIR /app

COPY uwsgi.ini .

COPY requirements.txt .

RUN pip install -r requirements.txt