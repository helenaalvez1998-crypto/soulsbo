FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=8080 \
    DATA_DIR=/data \
    DB_PATH=/data/colizeu.db

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates tzdata \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --gid 10001 soulsbo \
    && useradd --uid 10001 --gid 10001 --create-home --shell /usr/sbin/nologin soulsbo \
    && mkdir -p /data /tmp/soulsbo \
    && chown -R 10001:10001 /data /tmp/soulsbo /app

COPY requirements.txt ./requirements.txt
RUN python -m pip install --upgrade pip \
    && python -m pip install -r requirements.txt

COPY --chown=10001:10001 . .
COPY --chown=10001:10001 deploy/docker-entrypoint.sh /usr/local/bin/soulsbo-entrypoint
RUN chmod 0755 /usr/local/bin/soulsbo-entrypoint \
    && chown -R 10001:10001 /data

USER 10001:10001
EXPOSE 8080
VOLUME ["/data"]
ENTRYPOINT ["/usr/local/bin/soulsbo-entrypoint"]
CMD ["python", "bot.py"]
