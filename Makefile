DISTRO ?= debian:bookworm
PYTHON_VERSION ?= 3.12
VERSION ?= $(shell tr -d '[:space:]' < src/screamshotter/VERSION 2>/dev/null || echo "2.2.6")

build_deb:
	docker pull $(DISTRO)
	docker build -t screamshotter_deb -f .docker/Dockerfile.debian.builder \
		--build-arg DISTRO=$(DISTRO) \
		--build-arg PYTHON_VERSION=$(PYTHON_VERSION) \
		--build-arg VERSION=$(VERSION) .
	docker run --name screamshotter_deb_run -t screamshotter_deb bash -c "exit"
	docker cp screamshotter_deb_run:/dpkg ./
	docker stop screamshotter_deb_run
	docker rm screamshotter_deb_run

deps:
	docker compose run --remove-orphans --no-deps --rm web bash -c "cd .. && uv pip compile setup.py -o requirements.txt && uv pip compile requirements-dev.in -o requirements-dev.txt"
