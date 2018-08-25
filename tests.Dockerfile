FROM python:3.7.0-alpine

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY requirements-test.txt .
RUN pip install -r requirements-test.txt
