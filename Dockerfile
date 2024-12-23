FROM python:3.12-alpine
LABEL maintainer="bondarevskiymaks@gmail.com"

ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt requirements.txt

RUN pip install -r requirements.txt
RUN pip install psycopg

COPY . .
RUN mkdir -p /files/media

RUN adduser \
    --disabled-password \
    --no-create-home \
    regular_user

RUN chown -R regular_user /files/media
RUN chmod -R 755 /files/media


USER regular_user
