FROM python:3.9

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV DOCKER 1

RUN mkdir -p /code
COPY requirements.txt /tmp/requirements.txt
WORKDIR /code
RUN set -ex && \
    pip install --upgrade pip && \
    pip install -r /tmp/requirements.txt && \
    rm -rf /root/.cache/

RUN apt-get update && \
    apt-get install -y \
        postgresql-client \
        supervisor

COPY . /code/

EXPOSE 8000
CMD supervisord -c /code/catalog/supervisord.conf