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
ENV PLAYWRIGHT_BROWSERS_PATH=/opt/playwright
ENV PATH=/opt/venv/bin:$PATH

WORKDIR /opt/screamshotter
RUN mkdir -p /opt/screamshotter/var/log /opt/screamshotter/var/cache /opt/playwright /opt/screamshotter/static
RUN useradd -m -d /opt/screamshotter -s /bin/false -u 1001 screamshotter && chown screamshotter:screamshotter -R /opt

RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get -qq update && apt-get install -qq -y \
        ca-certificates \
        fonts-liberation \
        xdg-utils \
        git wget less nano curl \
        gettext \
        tini

COPY .docker/entrypoint.sh /usr/local/bin
RUN chmod +x /usr/local/bin/entrypoint.sh

EXPOSE 8000
WORKDIR /opt/screamshotter/src
ENTRYPOINT ["/usr/bin/tini", "--", "entrypoint.sh"]

FROM base AS build

ARG PYTHON_VERSION=3.14

RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get -qq update && apt-get install -qq -y \
        build-essential \
        libmagic1 \
        unzip

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

ENV UV_PYTHON_INSTALL_DIR=/opt/python

RUN uv python install ${PYTHON_VERSION} --install-dir ${UV_PYTHON_INSTALL_DIR}

RUN uv venv /opt/venv --python ${PYTHON_VERSION}
ENV UV_PYTHON=/opt/venv/bin/python
ENV UV_LINK_MODE=copy
ENV UV_CACHE_DIR=/opt/screamshotter/var/cache/

RUN --mount=type=bind,src=./requirements.txt,dst=/requirements.txt \
    --mount=type=cache,target=/opt/screamshotter/var/cache/,sharing=locked,uid=1001,gid=1001 \
    uv pip install --python /opt/venv/bin/python -r /requirements.txt

RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    /opt/venv/bin/playwright install --with-deps chromium && \
    chmod -R a+rX /opt/playwright
WORKDIR /opt/screamshotter
COPY pyproject.toml /opt/screamshotter/pyproject.toml
COPY src /opt/screamshotter/src


FROM build AS dev

RUN --mount=type=bind,src=./requirements-dev.txt,dst=/requirements-dev.txt \
    --mount=type=cache,target=/opt/screamshotter/var/cache/,sharing=locked,uid=1001,gid=1001 \
    uv pip install -r /requirements-dev.txt


WORKDIR /opt/screamshotter/src
CMD ["./manage.py", "runserver", "0.0.0.0:8000"]

FROM base AS prod

COPY --from=build /opt/python /opt/python
COPY --from=build /opt/venv /opt/venv
COPY --from=build /opt/playwright /opt/playwright
COPY src /opt/screamshotter/src
COPY pyproject.toml /opt/screamshotter/pyproject.toml

RUN mkdir -p /opt/screamshotter/static && chown -R screamshotter:screamshotter /opt/screamshotter

RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    /opt/venv/bin/playwright install-deps chromium && \
    apt-get upgrade -qq -y && \
    apt-get clean all && rm -rf /var/lib/apt/lists/* && rm -rf /var/cache/apt/*

VOLUME /opt/screamshotter/static

USER screamshotter

WORKDIR /opt/screamshotter/src

CMD gunicorn screamshotter.wsgi:application -w $WORKERS --max-requests $MAX_REQUESTS --timeout `expr $TIMEOUT + 25` --bind 0.0.0.0:8000 --worker-tmp-dir /dev/shm
