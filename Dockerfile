FROM python:3.9

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV DOCKER 1

# Allow catalog_env to be altered at build time and then passed through to the container.
ARG CATALOG_ENV=production
ENV CATALOG_ENV=$CATALOG_ENV

EXPOSE 8000

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
        supervisor \
        cron


COPY . /code/

# Copy the crontab into place and set permissions.
COPY catalog/crontab /etc/cron.d/catalog-cron
RUN chmod 0644 /etc/cron.d/catalog-cron

# Then run the server.
CMD supervisord -c /code/catalog/supervisord.conf