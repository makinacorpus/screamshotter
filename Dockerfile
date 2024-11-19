ARG BASE_IMAGE=noble

FROM ubuntu:${BASE_IMAGE} AS base

ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive
ENV LANG=C.UTF-8
ENV TZ=UTC
ENV COLLECTSTATIC=1
ENV TIMEOUT=60
ENV WORKERS=1
ENV MAX_REQUESTS=250
ENV PUPPETEER_CACHE_DIR=/app/puppeteer/

RUN useradd -ms /bin/bash django
RUN mkdir -p /app/static /opt
RUN chown django:django /app /opt

RUN apt-get -qq update && apt-get install -qq -y \
    libappindicator3-1 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libc6 \
    libcairo2 \
    libcups2 \
    libdbus-1-3 \
    libexpat1 \
    libfontconfig1 \
    libgcc1 \
    libgdk-pixbuf2.0-0 \
    libglib2.0-0 \
    libgtk-3-0 \
    libnspr4 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libstdc++6 \
    libx11-6 \
    libx11-xcb1 \
    libxcb1 \
    libxcomposite1 \
    libxcursor1 \
    libxdamage1 \
    libxext6 \
    libxfixes3 \
    libxi6 \
    libxrandr2 \
    libxrender1 \
    libxss1 \
    libxtst6 \
    ca-certificates \
    fonts-liberation \
    libnss3 \
    lsb-release \
    xdg-utils \
    git wget less nano curl \
    ca-certificates \
    gettext \
    libgbm-dev && \
    apt-get -q -y full-upgrade && \
    apt-get clean all && rm -rf /var/apt/lists/* && rm -rf /var/cache/apt/*

COPY .docker/entrypoint.sh /usr/local/bin

EXPOSE 8000
WORKDIR /app/src
ENTRYPOINT ["entrypoint.sh"]

FROM base AS build

ARG NODE_ENV=production

RUN apt-get -qq update && apt-get install -qq -y \
    build-essential \
    python3-pip python3-dev python3-venv libmagic1 && \
    apt-get clean all && rm -rf /var/apt/lists/* && rm -rf /var/cache/apt/*

USER django
RUN python3 -m venv /opt/venv
RUN /opt/venv/bin/pip3 install --no-cache-dir pip setuptools wheel -U

COPY requirements.txt /app/
RUN /opt/venv/bin/pip3 install --no-cache-dir -r /app/requirements.txt -U && rm /app/requirements.txt
RUN /opt/venv/bin/nodeenv /app/venv/ -C '' -p -n 20.9.0

# upgrade npm & requirements
COPY package.json /app/package.json
COPY package-lock.json /app/package-lock.json
RUN . /opt/venv/bin/activate && npm ci && rm /app/*.json

FROM build AS dev

COPY requirements-dev.txt /app/
RUN /opt/venv/bin/pip3 install --no-cache-dir -r /app/requirements-dev.txt -U && rm /app/requirements-dev.txt

CMD ["./manage.py", "runserver", "0.0.0.0:8000"]

FROM base

COPY --from=build /opt/venv /opt/venv
COPY --from=build /app/node_modules /app/node_modules
COPY --from=build /app/puppeteer /app/puppeteer
COPY src /app/src

RUN mkdir -p /app/static && chown django:django /app/static

RUN apt-get -qq update && apt-get upgrade -qq -y && \
    apt-get clean all && rm -rf /var/apt/lists/* && rm -rf /var/cache/apt/*

VOLUME /app/static

USER django

CMD gunicorn screamshotter.wsgi:application -w $WORKERS --max-requests $MAX_REQUESTS  --timeout `expr $TIMEOUT + 10` --bind 0.0.0.0:8000 --worker-tmp-dir /dev/shm
