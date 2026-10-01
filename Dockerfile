ARG BASE_IMAGE=ubuntu:resolute
ARG PYTHON_VERSION=3.14

FROM ${BASE_IMAGE} AS base

# add labels
LABEL org.opencontainers.image.authors="Makina Corpus"
LABEL org.opencontainers.image.source="https://github.com/makinacorpus/screamshotter/"
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
ENV NODE_PATH=/opt/screamshotter/node_modules/
ENV NODE_BIN_PATH=/opt/venv/bin/node
ENV PATH=/opt/venv/bin:$PATH

WORKDIR /opt/screamshotter
RUN mkdir -p /opt/screamshotter/var/log /opt/screamshotter/var/cache /opt/screamshotter/puppeteer /opt/screamshotter/static
RUN useradd -m -d /opt/screamshotter -s /bin/false -u 1001 screamshotter && chown screamshotter:screamshotter -R /opt

RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get -qq update && apt-get install -qq -y \
        libappindicator3-1 \
        libasound2-dev \
        libatk1.0-0t64 \
        libatk-bridge2.0-0 \
        libc6 \
        libcairo2 \
        libcups2t64 \
        libdbus-1-3 \
        libexpat1 \
        libfontconfig1 \
        libgcc-s1 \
        libgdk-pixbuf-2.0-0 \
        libglib2.0-0 \
        libgtk-3-0t64 \
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
        gettext \
        libgbm-dev

COPY .docker/entrypoint.sh /usr/local/bin
RUN chmod +x /usr/local/bin/entrypoint.sh

EXPOSE 8000
WORKDIR /opt/screamshotter/src
ENTRYPOINT ["entrypoint.sh"]

FROM base AS build

ARG NODE_ENV=production
ARG PYTHON_VERSION=3.14

RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get -qq update && apt-get install -qq -y \
        build-essential \
        libmagic1

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

ENV UV_PYTHON_INSTALL_DIR=/opt/python

RUN uv python install ${PYTHON_VERSION} --install-dir ${UV_PYTHON_INSTALL_DIR}

RUN uv venv /opt/venv --python ${PYTHON_VERSION}
ENV UV_PYTHON=/opt/venv/bin/python
ENV UV_LINK_MODE=copy
ENV UV_CACHE_DIR=/opt/screamshotter/var/cache/

RUN --mount=type=bind,src=./requirements.txt,dst=/requirements.txt \
    --mount=type=cache,target=/opt/screamshotter/var/cache/,sharing=locked,uid=1001,gid=1001 \
    uv pip install --python /opt/venv/bin/python "setuptools<81" wheel && \
    uv pip install --python /opt/venv/bin/python -r /requirements.txt

RUN /opt/venv/bin/nodeenv -C '' -p -n 24.21.0 --with-npm

WORKDIR /opt/screamshotter
COPY package.json /opt/screamshotter/package.json
COPY package-lock.json /opt/screamshotter/package-lock.json

RUN --mount=type=cache,target=/root/.npm \
    export PATH="/opt/venv/bin:$PATH" && \
    export PUPPETEER_CACHE_DIR=/opt/screamshotter/puppeteer/ && \
    npm ci --omit=dev --ignore-scripts && \
    node -e "import('puppeteer/internal/node/install.js').then(m => m.downloadBrowser()).then(() => process.exit(0))" && \
    chmod -R a+rX /opt/screamshotter/puppeteer && \
    rm -f /opt/screamshotter/*.json

COPY setup.py /opt/screamshotter/setup.py
COPY src /opt/screamshotter/src
RUN uv pip install --no-cache --no-deps --python /opt/venv/bin/python /opt/screamshotter

FROM build AS dev

RUN --mount=type=bind,src=./requirements-dev.txt,dst=/requirements-dev.txt \
    --mount=type=cache,target=/opt/screamshotter/var/cache/,sharing=locked,uid=1001,gid=1001 \
    uv pip install -r /requirements-dev.txt


WORKDIR /opt/screamshotter/src
CMD ["./manage.py", "runserver", "0.0.0.0:8000"]

FROM base AS prod

COPY --from=build /opt/python /opt/python
COPY --from=build /opt/venv /opt/venv
COPY --from=build /opt/screamshotter/node_modules /opt/screamshotter/node_modules
COPY --from=build /opt/screamshotter/puppeteer /opt/screamshotter/puppeteer
COPY src /opt/screamshotter/src
COPY setup.py /opt/screamshotter/setup.py

RUN mkdir -p /opt/screamshotter/static && chown -R screamshotter:screamshotter /opt/screamshotter

RUN apt-get -qq update && apt-get upgrade -qq -y && \
    apt-get clean all && rm -rf /var/apt/lists/* && rm -rf /var/cache/apt/*

VOLUME /opt/screamshotter/static

USER screamshotter

WORKDIR /opt/screamshotter/src

CMD gunicorn screamshotter.wsgi:application -w $WORKERS --max-requests $MAX_REQUESTS --timeout `expr $TIMEOUT + 10` --bind 0.0.0.0:8000 --worker-tmp-dir /dev/shm
