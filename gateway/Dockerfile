FROM tiangolo/uwsgi-nginx-flask:python3.8-alpine

COPY custom.conf /etc/nginx/conf.d/custom.conf

WORKDIR /app

COPY uwsgi.ini .

COPY requirements.txt .
RUN pip install -r requirements.txt
