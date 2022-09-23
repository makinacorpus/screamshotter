builder:
	docker build . -f ./Dockerfile.debian.builder --build-arg DISTRO=$(DISTRO) --build-arg BUILDID=$(BUILDID) -t screamshotter-builder
	mkdir -p dist
	docker run --rm screamshotter-builder tar -C /dpkg -c . | tar -C dist -xv