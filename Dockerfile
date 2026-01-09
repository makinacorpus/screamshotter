ARG BASE_IMAGE=ubuntu:noble
ARG PYTHON_VERSION=3.12

FROM ${BASE_IMAGE} AS base

# add labels
LABEL org.opencontainers.image.authors="Makina Corpus"
LABEL org.opencontainers.image.source="https://github.com/makinacorus/screamshotter/"
LABEL org.opencontainers.image.vendor="Makina Corpus"
LABEL org.opencontainers.image.licenses="BSD-2-Clause"
LABEL org.opencontainers.image.title="Screamshotter"
LABEL org.opencontainers.image.description="Take screenshot from site web."

ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive
ENV LANG=C.UTF-8
ENV TZ=UTC
ENV COLLECTSTATIC=1
ENV TIMEOUT=60
ENV WORKERS=1
ENV MAX_REQUESTS=250
ENV PUPPETEER_CACHE_DIR=/opt/screamshotter/puppeteer/
ENV UV_PYTHON_INSTALL_DIR=/opt

WORKDIR /opt/screamshotter
RUN mkdir -p /opt/screamshotter/var/log /opt/screamshotter/var/cache
RUN useradd -m -d /opt/screamshotter -s /bin/false -u 1001 screamshotter && chown screamshotter:screamshotter -R /opt

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

USER screamshotter
RUN uv python install ${PYTHON_VERSION}
USER root

RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get -qq update && apt-get install -qq -y \
        libappindicator3-1 \
        libasound2-dev \
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
        libgbm-dev

COPY .docker/entrypoint.sh /usr/local/bin

EXPOSE 8000
WORKDIR /app/src
ENTRYPOINT ["entrypoint.sh"]

FROM base AS build

ARG NODE_ENV=production
ARG PYTHON_VERSION=3.12

RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get -qq update && apt-get install -qq -y \
        build-essential \
        libmagic1

USER screamshotter

RUN uv venv -p $PYTHON_VERSION /opt/venv
ENV UV_PYTHON=/opt/venv/bin/python
ENV UV_LINK_MODE=copy
ENV UV_CACHE_DIR=/opt/screamshotter/var/cache/

RUN --mount=type=bind,src=./requirements.txt,dst=/requirements.txt \
    --mount=type=cache,target=/opt/screamshotter/var/cache/,sharing=locked,uid=1001,gid=1001 \
    uv pip install -r /requirements.txt && /opt/venv/bin/nodeenv /opt/venv/ -C '' -p -n 20.9.0
COPY requirements.txt /app/
RUN /opt/venv/bin/pip3 install --no-cache-dir -r /app/requirements.txt -U && rm /app/requirements.txt
RUN /opt/venv/bin/nodeenv /app/venv/ -C '' -p -n 22.19.0

# upgrade npm & requirements
COPY package.json /app/package.json
COPY package-lock.json /app/package-lock.json
RUN . /opt/venv/bin/activate && npm ci && rm /app/*.json
RUN . /opt/venv/bin/activate && npx puppeteer browsers install chrome
COPY package.json /opt/screamshotter/package.json
COPY package-lock.json /opt/screamshotter/package-lock.json
WORKDIR /opt/screamshotter
RUN . /opt/venv/bin/activate && npm ci && rm /opt/screamshotter/*.json

FROM build AS dev

RUN --mount=type=bind,src=./requirements-dev.txt,dst=/requirements-dev.txt \
    --mount=type=cache,target=/opt/screamshotter/var/cache/,sharing=locked,uid=1001,gid=1001 \
    uv pip install -r /requirements-dev.txt

WORKDIR /opt/screamshotter/src
CMD ["./manage.py", "runserver", "0.0.0.0:8000"]

FROM base AS prod

COPY --from=build /opt/venv /opt/venv
COPY --from=build /app/node_modules /app/node_modules
COPY --from=build /app/puppeteer /app/puppeteer
COPY src /app/src

RUN mkdir -p /app/static && chown django:django /app/static

RUN apt-get -qq update && apt-get upgrade -qq -y && \
    apt-get clean all && rm -rf /var/apt/lists/* && rm -rf /var/cache/apt/*

VOLUME /app/static

USER screamshotter

CMD gunicorn screamshotter.wsgi:application -w $WORKERS --max-requests $MAX_REQUESTS  --timeout `expr $TIMEOUT + 10` --bind 0.0.0.0:8000 --worker-tmp-dir /dev/shm
