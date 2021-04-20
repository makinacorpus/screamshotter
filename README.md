[![codecov](https://codecov.io/gh/makinacorpus/screamshotter/branch/master/graph/badge.svg?token=Vk72Ni1u8F)](https://codecov.io/gh/makinacorpus/screamshotter)
![github actions](https://github.com/makinacorpus/screamshotter/actions/workflows/test.yml/badge.svg)

# Screamshotter : microservice to take webpage screenshots

### Powered by Django / Node / Puppeteer / Chromium

# INSTALL

## Ubuntu

### From apt repo

```
sudo apt update
sudo apt install wget software-properties-common
echo "deb [arch=amd64] https://packages.geotrek.fr/ubuntu $(lsb_release -sc) main" | sudo tee /etc/apt/sources.list.d/geotrek.list
wget -O- "https://packages.geotrek.fr/geotrek.gpg.key" | sudo apt-key add -
sudo apt update
sudo apt install screamshotter
```

### Local installation

Download deb package  from last release assets

Example:

```bash
wget https://github.com/makinacorpus/screamshotter/releases/download/1.9.9-beta0/screamshotter_1.9.9.ubuntu18.04.dev752653563_amd64.deb
```

Install it

```bash
sudo dpkg -i screamshotter_1.9.9.ubuntu18.04.dev752653563_amd64.deb
```

Fix dependencies

```bash
sudo apt install -f
```

## Docker

```
docker pull makinacorpus/screamshotter:latest
```

# USAGE

## ubuntu

with systemd

```
systemctl status|stop|start screamshotter
```

## docker

```
docker run -d -p 8000:8000 makinacorpus/screamshotter:latest
```

## make screenshots

```
curl -d url=https://google.com http://127.0.0.1:8000 > google.png
```

## access test browsable api

```
http://127.0.0.1:8000/?format=api
```

# DEVELOPMENT

## Docker

```
git clone git@github.com:makinacorpus/screamshotter.git
cd screamshotter
docker-compose up
```

## Tools

### pip-tools

keep dependencies up to date with pip-tools

```bash
# pip install pip-tools
pip-compile --upgrade
```

## Quality

### flake8

```bash
# pip install flake8
flake8 src
```

### eslint

```bash
# use nodeenv node & npm
npm run lint
```
