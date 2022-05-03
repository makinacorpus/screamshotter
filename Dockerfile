FROM ubuntu:focal as base

ENV PYTHONUNBUFFERED 1
ENV DEBIAN_FRONTEND noninteractive
ENV LANG C.UTF-8
ENV COLLECTSTATIC 1
ENV TIMEOUT 60
ENV WORKERS 1

RUN useradd -ms /bin/bash django
RUN mkdir -p /app
RUN chown django:django /app

RUN apt-get -qq update && apt-get install -qq -y \
    gconf-service \
    libasound2 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libc6 \
    libcairo2 \
    libcups2 \
    libdbus-1-3 \
    libexpat1 \
    libfontconfig1 \
    libgcc1 \
    libgconf-2-4 \
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
    libappindicator1 \
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

FROM base as build

ARG NODE_ENV=production

RUN apt-get -qq update && apt-get install -qq -y \
    build-essential \
    python3.8-dev python3.8-venv python3.8-distutils && \
    apt-get clean all && rm -rf /var/apt/lists/* && rm -rf /var/cache/apt/*

# install pip & requirements
RUN wget https://bootstrap.pypa.io/get-pip.py && python3.8 get-pip.py && rm get-pip.py

USER django
RUN python3.8 -m venv /app/venv
RUN /app/venv/bin/pip3 install --no-cache-dir pip setuptools wheel -U

COPY requirements.txt /app/
RUN /app/venv/bin/pip3 install --no-cache-dir -r /app/requirements.txt -U && rm /app/requirements.txt
RUN /app/venv/bin/nodeenv /app/venv/ -C '' -p -n 16.15.0

# upgrade npm & requirements
COPY package.json /app/package.json
COPY package-lock.json /app/package-lock.json
RUN . /app/venv/bin/activate && npm ci && rm /app/*.json

FROM build as dev

COPY requirements-dev.txt /app/
RUN /app/venv/bin/pip3 install --no-cache-dir -r /app/requirements-dev.txt -U && rm /app/requirements-dev.txt

CMD ["./manage.py", "runserver", "0.0.0.0:8000"]

FROM base

COPY --from=build /app/venv /app/venv
COPY --from=build /app/node_modules /app/node_modules
COPY src /app/src

RUN mkdir -p /app/static && chown django:django /app/static

RUN apt-get -qq update && apt-get upgrade -qq -y && \
    apt-get clean all && rm -rf /var/apt/lists/* && rm -rf /var/cache/apt/*

VOLUME /app/static

USER django

HEALTHCHECK CMD curl http://127.0.0.1:8000/?format=api || exit 1

CMD gunicorn screamshotter.wsgi:application -w $WORKERS --timeout $TIMEOUT --bind 0.0.0.0:8000 --worker-tmp-dir /dev/shm

