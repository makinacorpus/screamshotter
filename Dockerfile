FROM ubuntu:focal

ENV PYTHONUNBUFFERED 1
ENV DEBIAN_FRONTEND noninteractive
ENV LANG C.UTF-8
ENV SECRET_KEY dev-dev-dev
ARG NODE_ENV=production
RUN useradd -ms /bin/bash django
RUN mkdir -p /app

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
    build-essential \
    git wget less nano curl \
    ca-certificates \
    gettext \
    libgbm-dev \
    python3.8-dev python3.8-venv python3.8-distutils -- && \
    apt-get clean all && rm -rf /var/apt/lists/* && rm -rf /var/cache/apt/*

# install pip & requirements
RUN wget https://bootstrap.pypa.io/get-pip.py && python3.8 get-pip.py && rm get-pip.py
RUN python3.8 -m venv /app/venv
RUN /app/venv/bin/pip3 install pip setuptools wheel -U

COPY requirements.txt /requirements.txt
RUN /app/venv/bin/pip3 install --no-cache-dir -r /requirements.txt -U
RUN /app/venv/bin/nodeenv -C '' -p -n 14.15.5

# upgrade npm & requirements
COPY package.json /package.json
COPY package-lock.json /package-lock.json
RUN . /app/venv/bin/activate && npm ci

COPY src /app/src
COPY app.json /app/src/app.json

RUN chown django:django -R /app

USER django

EXPOSE 8000

WORKDIR /app/src


CMD ["gunicorn", "project.wsgi:application", "--bind", "0.0.0.0:8000"]
