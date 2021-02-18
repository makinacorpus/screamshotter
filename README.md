# INSTALL

## Ubuntu

```
sudo apt update
sudo apt install wget software-properties-common
echo "deb [arch=amd64] https://packages.geotrek.fr/ubuntu $(lsb_release -sc) main" | sudo tee /etc/apt/sources.list.d/geotrek.list
wget -O- "https://packages.geotrek.fr/geotrek.gpg.key" | sudo apt-key add -
sudo apt update
sudo apt install screamshotter
```

## Docker

```
git clone https://github.com/makinacorpus/screamshotter.git
cd screamshotter
ln -s docker-compose-prod.yml docker-compose.yml
docker-compose up
```

# RUN

# USAGE

# DEVELOPMENT

## Docker

```
git clone git@github.com:makinacorpus/screamshotter.git
cd screamshotter
ln -s docker-compose-dev.yml docker-compose.yml
docker-compose up
```

## Tools

### pip-tools

keep dependencies up to date with pip-tools

### node / npm

## Quality

### flake8

flake8 .

### eslint

eslint .
