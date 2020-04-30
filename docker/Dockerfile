FROM python:3.7.1

LABEL Author="Mikael"
LABEL E-mail="mihai.constantinescu@madintelligence.ro"
LABEL version="7.9"

RUN mkdir /app
WORKDIR /app

COPY . .
RUN pip install -r requirements.txt
EXPOSE 7555

ENTRYPOINT ["python", "run.py", "-n", "--rundir=/app", "scrapy-do", "--config=/app/server.conf"]