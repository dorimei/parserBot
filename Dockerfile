FROM python:3.9-slim as builder

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc

COPY requirements.txt .
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /app/wheels -r requirements.txt

# Финальный этап
FROM python:3.9-slim

WORKDIR /app

ENV API_TOKEN ""
ENV STATE_FILE "/app/files/state.json"
ENV LINKS_FILE "/app/files/links.txt"
ENV LANG ru_RU.UTF-8
ENV LANGUAGE ru_RU:ru
ENV LC_ALL ru_RU.UTF-8

COPY --from=builder /app/wheels /wheels
COPY --from=builder /app/requirements.txt .
COPY . .
COPY ./links.txt /app/files/links.txt

RUN pip install --no-cache /wheels/*
ENTRYPOINT python bot.py -s $STATE_FILE -n $LINKS_FILE $API_TOKEN