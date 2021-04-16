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
docker run -d -p 8000:8000 makinacorpus/screamshotter:latest
```

# RUN

# USAGE

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

### node / npm

## Quality

### flake8

```bash
# pip install flake8
flake8 src
```

### eslint

```bash
# pip install flake8
npm run lint
```
