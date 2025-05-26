# syntax=docker/dockerfile:1

FROM python:3.13.3-alpine

WORKDIR /app

RUN apk update && apk add git

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

COPY . .

CMD [ "python3", "organizerbot.py"]